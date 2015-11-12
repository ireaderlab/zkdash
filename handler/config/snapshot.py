#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014,掌阅科技
All rights reserved.

摘    要: snapshot.py
创 建 者: zhuangshixiong
创建日期: 2015-06-16
"""
import json
from tornado.web import authenticated

from handler.bases import CommonBaseHandler
from handler.bases import ArgsMap
from lib import route
from lib.utils import normalize_path
from model.db.zd_zookeeper import ZdZookeeper
from model.db.zd_snapshot import ZdSnapshot
from service import snapshot as SnapshotService
from service.snapshot import MakeSnapshotError
from conf import log


############################################################
# UI
############################################################

@route(r'/config/snapshot/index', '查看')
class ZdSnapshotIndexHandler(CommonBaseHandler):

    '''index, 查看
    '''

    @authenticated
    def response(self):
        '''index
        '''
        # zookeeper clusters
        clusters = ZdZookeeper.select().where(ZdZookeeper.deleted == "0")
        if clusters.count() < 1:
            return self.ajax_popup(code=300, msg="请先到zookeeper管理菜单下设置集群信息！")
        return self.render('config/snapshot/index.html',
                           clusters=clusters)


@route(r'/config/snapshot/displaytree')
class ZdSnapshotTreeHandler(CommonBaseHandler):

    """tree
    """
    args_list = [
        ArgsMap('cluster_name', required=True),
        ArgsMap('path', default="/"),
    ]

    @authenticated
    def response(self):
        """返回指定zookeeper集群的znode信息
        """
        normalized_path = normalize_path(self.path)
        nodes = SnapshotService.get_snapshot_tree(self.cluster_name, normalized_path)
        if not nodes:
            return self.ajax_popup(code=300, msg="对不起，该节点路径下（%s）无快照数据！" % self.path)

        znodes_data = json.dumps(nodes)
        return self.render('config/snapshot/displaytree.html',
                           cluster_name=self.cluster_name,
                           znodes_data=znodes_data)


@route(r'/config/snapshot/view')
class ZdSnapshotViewHandler(CommonBaseHandler):

    '''view
    '''
    args_list = [
        ArgsMap('cluster_name', required=True),
        ArgsMap('path', required=True)
    ]

    @authenticated
    def response(self):
        '''zookeeper上znode快照的查看
        '''
        status_mapping = {
            "0": "备份中",
            "1": "最近使用"
        }
        snapshots = ZdSnapshot.select().where(
            (ZdSnapshot.cluster_name == self.cluster_name) &
            (ZdSnapshot.path == self.path) &
            (ZdSnapshot.deleted == "0")
        ).order_by(ZdSnapshot.create_time)
        return self.render('config/snapshot/view.html',
                           status_mapping=status_mapping,
                           path=self.path,
                           snapshots=snapshots)


############################################################
# API
############################################################

@route(r'/config/snapshot/save')
class ZdSnapshotSaveHandler(CommonBaseHandler):
    """save
    """
    args_list = [
        ArgsMap('cluster_name', required=True),
        ArgsMap('path', default='')
    ]

    @authenticated
    def response(self):
        '''add
        '''
        try:
            SnapshotService.make_snapshot(self.cluster_name, self.path)
            return self.ajax_ok(close_current=False)
        except MakeSnapshotError:
            return self.ajax_popup(code=300, msg="父节点快照尚未生成，无法创建快照！")


@route(r'/config/snapshot/delete', '删除')
class ZdSnapshotDeleteHandler(CommonBaseHandler):

    """delete, 删除
    """
    args_list = [
        ArgsMap('id', required=True),
    ]

    @authenticated
    def response(self):
        '''delete
        '''
        try:
            ZdSnapshot.one(id=self.id).delete_instance()
            return self.ajax_ok(close_current=True)
        except Exception as exc:
            log.error("error occurred while delete snapshot, id: %s\n%s", self.id, str(exc))
            return self.ajax_popup(code=300, msg="删除快照出错啦！")


@route(r'/config/snapshot/addsnapshots')
class WsZnodeAddSnapshotHandler(CommonBaseHandler):
    """批量生成快照
    """
    args_list = [
        ArgsMap('cluster_name', required=True),
        ArgsMap('path', default='/'),
    ]

    @authenticated
    def response(self):
        """根据父节点路径批量生成快照
        """
        try:
            SnapshotService.make_snapshots_from_path(self.cluster_name, self.path)
            return self.ajax_ok(close_current=False)
        except MakeSnapshotError:
            return self.ajax_popup(code=300, msg="父节点快照尚未生成，无法创建快照！")


@route(r'/config/snapshot/rollback', '回滚')
class ZdSnapshotRollbackHandler(CommonBaseHandler):

    """rollback
    """
    args_list = [
        ArgsMap('cluster_name', required=True),
        ArgsMap('path', required=True),
        ArgsMap('snapshot_id', default=""),
        ArgsMap('recursive', default=""),
    ]

    @authenticated
    def response(self):
        """rollback
        """
        if self.snapshot_id:
            snapshot = ZdSnapshot.one(id=self.snapshot_id)
        else:
            snapshot = SnapshotService.last_snapshot(self.cluster_name, self.path)
        # 检查快照是否存在
        if not snapshot:
            return self.ajax_popup(code=300, msg="快照未找到，请手动查看一下")

        if self.recursive == "1":
            # 递归回滚快照
            SnapshotService.rollback_snapshots_recursively(self.cluster_name, snapshot)
        else:
            SnapshotService.rollback_snapshot(self.cluster_name, snapshot)
        return self.ajax_ok(close_current=False)


@route(r'/config/snapshot/deletenodes')
class WsSnapshotDeleteNodesHandler(CommonBaseHandler):
    """删除快照节点树形结构信息
    """
    args_list = [
        ArgsMap('cluster_name', required=True),
        ArgsMap('node_path', required=True),
        ArgsMap('recursive', default='0')
    ]

    @authenticated
    def response(self):
        """删除树节点节点
        """
        err_msg = SnapshotService.delete_snapshot_nodes(self.cluster_name,
                                                        self.node_path,
                                                        self.recursive)
        if err_msg:
            return self.ajax_popup(code=300, msg=err_msg)
        else:
            return self.ajax_ok(close_current=False)
