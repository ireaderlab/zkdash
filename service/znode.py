#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Copyright (c) 2014,掌阅科技
All rights reserved.

摘    要: znode.py
创 建 者: zhuangshixiong
创建日期: 2015-07-24
说明:     在对zookeeper数据操作基础上增加业务逻辑处理（元数据保存和快照操作）
'''
import os
from kazoo.exceptions import NoNodeError

from lib.utils import normalize_path
from model.db.zd_znode import ZdZnode
from model.db.zd_snapshot import ZdSnapshot
from service import zookeeper as ZookeeperService
from service import snapshot as SnapshotService
from service.snapshot import MakeSnapshotError
from conf import log


def is_node_name_ok(node_name):
    """check if node name is ok
    """
    # 节点名不可包含`/`特殊字符
    node_name = node_name.strip('/')
    return node_name.find('/') == -1


def get_child_znodes(cluster_name, path):
    """get child znodes with extra info
    """
    zoo_client = ZookeeperService.get_zoo_client(cluster_name)
    child_znodes = []

    children = zoo_client.get_children(path)
    # iter child nodes and convert to dict with extra info
    for child in children:
        child_path = os.path.join(path, child)
        data, _ = zoo_client.get(child_path)
        # node
        node = {"path": child_path, "value": data}
        node["name"] = child_path.rsplit('/', 1)[-1]
        child_znodes.append(node)
    return child_znodes


def set_znode(cluster_name, path, data, znode_type='0', business=''):
    """更新或增加znode节点，包括存储于mysql的元数据和存储于zookeeper上的data
    """
    path = normalize_path(path)

    # 更新zookeeper上的数据
    ZookeeperService.set_or_create(cluster_name, path, data)

    # 在mysql上存储znode的相关元数据，节点类型和业务说明
    znode = ZdZnode.one(cluster_name=cluster_name, path=path, deleted="0")
    if znode is None:
        znode = ZdZnode(cluster_name=cluster_name, path=path)
    znode.type = znode_type
    znode.business = business
    znode.save()

    try:
        # 自动快照（如果配置信息没有变更，实际不会进行快照）
        SnapshotService.make_snapshot(cluster_name, path, data)
    except MakeSnapshotError as exc:
        log.error('make snapshot error: %s', str(exc))


def set_batch_znodes(cluster_name, parent_path, batch_data, business=''):
    """set batch znodes from python data
    """
    for key, data in batch_data:
        path = os.path.join(parent_path, key)
        set_znode(cluster_name, path, data, business=business)


def delete_znodes(cluster_name, path, recursive=False, del_snapshots=True):
    """delete znodes' meta info in mysql
    """
    del_znode_query = del_snapshot_query = None
    if recursive:
        # monkey patch for delete znodes recursively
        target_path = path.rstrip("/") + "/"
        del_znode_query = ZdZnode.delete().where(
            (ZdZnode.cluster_name == cluster_name) &
            ((ZdZnode.path.startswith(target_path)) | (ZdSnapshot.path == path))
        )
        del_snapshot_query = ZdSnapshot.delete().where(
            (ZdSnapshot.cluster_name == cluster_name) &
            ((ZdSnapshot.path.startswith(target_path)) | (ZdSnapshot.path == path))
        )
    else:
        del_znode_query = ZdZnode.delete().where(
            (ZdZnode.cluster_name == cluster_name) &
            (ZdZnode.path == path)
        )
        del_snapshot_query = ZdSnapshot.delete().where(
            (ZdSnapshot.cluster_name == cluster_name) &
            (ZdSnapshot.path == path)
        )
    del_znode_query.execute()
    if del_snapshots:
        del_snapshot_query.execute()


def delete_znodes_diff_with_keys(cluster_name, parent_path, keys):
    """删除给定路径下节点名不在传入keys的子节点
    """
    zoo_client = ZookeeperService.get_zoo_client(cluster_name)

    children = zoo_client.get_children(parent_path)
    diff_znodes = [child for child in children if child not in keys]
    for znode in diff_znodes:
        path = os.path.join(parent_path, znode)
        zoo_client.delete(path, version=-1, recursive=False)
        delete_znodes(cluster_name, path, recursive=False, del_snapshots=True)


def get_znode_tree(zoo_client, path, nodes, current_id='1', parent_id='0'):
    """get zookeeper nodes recursively, format as ztree data
    """
    # 节点名只取最末尾的名称
    name = path if path == "/" else path.rsplit('/', 1)[-1]
    nodes.append({
        "id": current_id,
        "pId": parent_id,
        "name": name,
        "path": path
    })

    try:
        children = zoo_client.get_children(path)
    except NoNodeError as exc:
        log.warning('Node does not exists on zookeeper: %s', path)
    else:
        for idx, child in enumerate(children):
            # 左填充0到数字, 避免树的广度过宽，id冲突错误, 01, 09...
            idx = '{0:02d}'.format(idx)
            # parent_id as 1, then child_id should be 10, 11, 12...
            child_id = "{0}{1}".format(current_id, idx)
            child_path = os.path.join(path, child)
            get_znode_tree(zoo_client, child_path, nodes, child_id, current_id)


def get_znode_tree_from_qconf(cluster_name, path, nodes, current_id='1', parent_id='0'):
    """get zookeeper nodes from qconf recursively, format as ztree data
    """
    from lib.zyqconf import qconf_py

    # 节点名只取最末尾的名称
    name = path if path == "/" else path.rsplit('/', 1)[-1]
    nodes.append({
        "id": current_id,
        "pId": parent_id,
        "name": name,
        "path": path
    })

    children = []
    try:
        children = qconf_py.get_batch_keys(path, cluster_name)
    except qconf_py.Error as exc:
        # fix bugs for qconf's get_batch_keys error while path is root path("/")
        if exc.message == "Error parameter!":
            zoo_client = ZookeeperService.get_zoo_client(cluster_name)
            children = zoo_client.get_children(path)
        else:
            log.warning('Node does not exists on QConf Agent, path: %s', path)

    for idx, child in enumerate(children):
        child_path = os.path.join(path, str(child))
        # 如果父节点ID为1，则它的子节点ID应为101, 102, 103(左填充0到数字, 避免树的广度过宽，id冲突错误, 01, 09...)
        child_id = "{0}{1:02d}".format(current_id, idx)
        get_znode_tree_from_qconf(cluster_name, child_path, nodes, child_id, current_id)


if __name__ == '__main__':
    pass
