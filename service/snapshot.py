#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Copyright (c) 2014,掌阅科技
All rights reserved.

摘    要: snapshot.py
创 建 者: zhuangshixiong
创建日期: 2015-06-17
说明:     zookeeper节点的快照信息存储（快照数据和快照节点树结构信息存储）
'''
import os
import hashlib
from datetime import datetime

from kazoo.exceptions import NoNodeError
from model.db.zd_snapshot import ZdSnapshot
from model.db.zd_snapshot_tree import ZdSnapshotTree
from service import zookeeper as ZookeeperService
from conf import log


class MakeSnapshotError(Exception):
    pass


#######################################################
# Helper function to get path info
#######################################################

def _extract_parent_path(node_path):
    """extract parent_path from path given
    """
    path_parts = node_path.strip('/').split('/')
    parent_path = '/' + '/'.join(path_parts[:-1])
    return parent_path


#######################################################
# Function to maintain tree structure
#######################################################

def _is_tree_node_exists(cluster_name, node_path):
    """check if node exists
    """
    return ZdSnapshotTree.one(cluster_name=cluster_name, node_path=node_path)


def _is_tree_leaf_node(cluster_name, node_path):
    """check if is leaf node
    """
    node = ZdSnapshotTree.one(cluster_name=cluster_name, node_path=node_path)
    if node and node.right == node.left + 1:
        return True
    else:
        return False


def _add_tree_root(cluster_name, node_path):
    """增加树形结构根节点，保持树形结构
    """
    root_node = ZdSnapshotTree(
        cluster_name=cluster_name,
        node_path=node_path,
        left=0,
        right=1
    )
    root_node.save()


def _add_tree_node(cluster_name, parent_node, node_path):
    """增加树形结构普通节点，需要保持树形结构
    """
    slot_left = parent_node.left
    # update left and right value
    update_left_query = ZdSnapshotTree.update(left=ZdSnapshotTree.left + 2).where(
        (ZdSnapshotTree.left > slot_left) &
        (ZdSnapshotTree.cluster_name == cluster_name)
    )
    update_right_query = ZdSnapshotTree.update(right=ZdSnapshotTree.right + 2).where(
        (ZdSnapshotTree.right > slot_left) &
        (ZdSnapshotTree.cluster_name == cluster_name)
    )
    update_left_query.execute()
    update_right_query.execute()
    # create new node
    child_node = ZdSnapshotTree(
        cluster_name=cluster_name,
        node_path=node_path,
        left=slot_left + 1,
        right=slot_left + 2)
    child_node.save()


def _get_tree_children_from_path(cluster_name, parent_path):
    """在快照树形结构表（zd_snapshot_tree）获取某个节点所有的子节点路径
    """
    sql_tpl = ("SELECT node.node_path FROM zd_snapshot_tree AS node, zd_snapshot_tree AS parent "
               "WHERE parent.cluster_name = %s AND parent.node_path = %s "
               "AND node.cluster_name = %s"
               "AND node.left BETWEEN parent.left AND parent.right")
    children = ZdSnapshotTree.raw(sql_tpl, cluster_name, parent_path, cluster_name)
    return [child.node_path for child in children]


#######################################################
# Function to manage snapshot
#######################################################

def last_snapshot(cluster_name, path):
    """获取上次保存的快照
    如有快照正在使用，选取的是离它时间最近的快照,
    否则为最新保存的快照
    """
    snapshots = ZdSnapshot.select().where(
        (ZdSnapshot.cluster_name == cluster_name) &
        (ZdSnapshot.path == path) &
        (ZdSnapshot.deleted == "0")
    ).order_by(ZdSnapshot.create_time)

    last_shot = None
    for snapshot in snapshots:
        if last_shot is None:
            last_shot = snapshot
        # status为1代表正在使用，0代表备份中
        if snapshot.status == "1":
            break
        last_shot = snapshot
    return last_shot


def is_snapshot_redundant(cluster_name, path, commit_md5):
    """
    检验快照是否重复生成
    """
    return ZdSnapshot.one(cluster_name=cluster_name,
                          path=path,
                          commit=commit_md5,
                          deleted="0")


def delete_snapshots(cluster_name, path, recursive='0'):
    """删除快照数据信息
    """
    if recursive == "1":
        # monkey patch for delete snapshots recursively
        target_path = path.rstrip("/") + "/"
        del_snapshot_query = ZdSnapshot.delete().where(
            (ZdSnapshot.cluster_name == cluster_name) &
            ((ZdSnapshot.path.startswith(target_path)) | (ZdSnapshot.path == path))
        )
    else:
        del_snapshot_query = ZdSnapshot.delete().where(
            (ZdSnapshot.cluster_name == cluster_name) &
            (ZdSnapshot.path == path)
        )
    del_snapshot_query.execute()


#######################################################
# Function to communicate with zookeeper
#######################################################

def _get_recursively(zoo_client, path, nodes):
    """get zookeeper nodes recursively
    """
    try:
        data, _ = zoo_client.get(path)
    except NoNodeError as exc:
        log.warning("No node exists in path: %s", path)
    else:
        nodes.append({"path": path, "data": data})
        for child in zoo_client.get_children(path):
            child_path = os.path.join(path, child)
            _get_recursively(zoo_client, child_path, nodes)


#######################################################
# 对外提供的操作函数
#######################################################

def make_snapshot(cluster_name, path, data=None):
    """生成快照，包括快照树结构信息(zd_snapshot_tree)和快照数据(zd_snapshot)
    """
    if data is None:
        data = ZookeeperService.get(cluster_name, path)

    # 验证节点路径是否已经存在，不存在才创建相应树结构节点
    if not _is_tree_node_exists(cluster_name, path):
        if path.strip() == "/":
            # 增加根节点
            _add_tree_root(cluster_name=cluster_name, node_path=path)
        else:
            # 增加子节点
            parent_path = _extract_parent_path(path)
            parent_node = ZdSnapshotTree.one(cluster_name=cluster_name, node_path=parent_path)
            if not parent_node:
                raise MakeSnapshotError("Parent node does not exists, could not build tree!")
            _add_tree_node(cluster_name=cluster_name,
                           parent_node=parent_node,
                           node_path=path)

    # 检验快照是否重复生成
    commit_md5 = hashlib.md5(data).hexdigest()
    if is_snapshot_redundant(cluster_name, path, commit_md5):
        log.warn("Snapshot already exists for znode in cluster: %s, path: %s", cluster_name, path)
        return
    # 保存快照信息
    snapshot = ZdSnapshot(cluster_name=cluster_name,
                          path=path,
                          data=data,
                          create_time=datetime.now(),
                          commit=commit_md5)
    snapshot.save()


def make_snapshots_from_path(cluster_name, path):
    """根据节点路径批量生成快照
    """
    zoo_client = ZookeeperService.get_zoo_client(cluster_name)
    nodes = []
    _get_recursively(zoo_client, path, nodes)
    for node in nodes:
        make_snapshot(cluster_name, node["path"], node["data"])


def rollback_snapshot(cluster_name, snapshot):
    """快照回滚
    """
    # 更新所有正在使用的快照为备份中, 0代表备份中，1代表使用中
    query = ZdSnapshot.update(status="0").where(
        (ZdSnapshot.cluster_name == cluster_name) &
        (ZdSnapshot.path == snapshot.path) &
        (ZdSnapshot.status == "1")
    )
    query.execute()
    # 根据快照数据更新zookeeper上znode的data
    ZookeeperService.set_or_create(cluster_name, snapshot.path, str(snapshot.data))
    # 更新回滚的快照状态为正在使用
    snapshot.status = "1"
    snapshot.save()


def rollback_snapshots_recursively(cluster_name, snapshot):
    """快照递归回滚
    """
    rollback_snapshot(cluster_name, snapshot)
    for child_path in _get_tree_children_from_path(cluster_name, snapshot.path):
        child_snapshot = last_snapshot(cluster_name, child_path)
        if child_snapshot:
            rollback_snapshot(cluster_name, child_snapshot)


def delete_snapshot_nodes(cluster_name, node_path, recursive='0'):
    """删除快照节点所有信息，包括树结构信息(zd_snapshot_tree)和快照数据(zd_znode_snapshot)
    """
    if recursive == '0' and not _is_tree_leaf_node(cluster_name, node_path):
        return "无法删除非叶子节点！"

    node = ZdSnapshotTree.one(cluster_name=cluster_name, node_path=node_path)
    if not node:
        return "节点不存在！"

    # 删除快照节点，同时维护树结构
    slot_left, slot_right = node.left, node.right
    slot_width = slot_right - slot_left
    del_query = ZdSnapshotTree.delete().where(
        (ZdSnapshotTree.left.between(slot_left, slot_right)) &
        (ZdSnapshotTree.cluster_name == cluster_name)
    )
    update_left_query = ZdSnapshotTree.update(left=ZdSnapshotTree.left - slot_width).where(
        (ZdSnapshotTree.left > slot_right) &
        (ZdSnapshotTree.cluster_name == cluster_name)
    )
    update_right_query = ZdSnapshotTree.update(right=ZdSnapshotTree.right - slot_width).where(
        (ZdSnapshotTree.right > slot_right) &
        (ZdSnapshotTree.cluster_name == cluster_name)
    )
    del_query.execute()
    update_left_query.execute()
    update_right_query.execute()
    # 删除快照信息
    delete_snapshots(cluster_name, node_path, recursive)


def get_snapshot_tree(cluster_name, parent_path="/"):
    """获取快照的树形结构信息

    数据库表结构设计参考: http://mikehillyer.com/articles/managing-hierarchical-data-in-mysql/

    """
    # 获取每个节点的路径和深度，节点返回结果是按照前序遍历顺序组织的
    sql_tpl = ("SELECT node.id, node.node_path, (COUNT(parent.node_path)-1) AS depth "
               "FROM zd_snapshot_tree AS node, zd_snapshot_tree AS parent "
               "WHERE node.cluster_name = '{0}' AND parent.cluster_name = '{0}' "  # 每个zk集群单独构建一棵树
               "AND node.node_path like '{1}%%' "
               "AND node.left BETWEEN parent.left AND parent.right "
               "GROUP BY node.node_path "
               "ORDER BY node.left")
    sql = sql_tpl.format(cluster_name, parent_path)
    records = ZdSnapshotTree.raw(sql)

    # 节点返回结果是按照前序遍历顺序组织的, 通过记录上层深度和节点id映射关系可以构造出树结构
    nodes = []
    last_depth_mapping = {}
    for record in records:
        last_depth_mapping[record.depth] = record.id
        parent_id = last_depth_mapping.get(record.depth - 1, -1)
        nodes.append({
            "id": record.id,
            "pId": parent_id,
            "name": record.node_path.rsplit('/', 1)[-1],
            "path": record.node_path
        })
    return nodes


if __name__ == '__main__':
    pass
