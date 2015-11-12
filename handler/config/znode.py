#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014,掌阅科技
All rights reserved.

摘    要: znode.py
创 建 者: zhuangshixiong
创建日期: 2015-06-16
"""
import os
import hashlib

import json
from tornado.web import authenticated
from kazoo.exceptions import NotEmptyError, BadArgumentsError

from handler.bases import CommonBaseHandler
from handler.bases import ArgsMap
from lib import route
from lib.utils import normalize_path
from model.db.zd_znode import ZdZnode
from model.db.zd_zookeeper import ZdZookeeper
from model.db.zd_qconf_feedback import ZdQconfFeedback
from service import zookeeper as ZookeeperService
from service import znode as ZnodeService
from conf.settings import USE_QCONF


############################################################
# UI
############################################################

@route(r'/config/znode/index', '查看')
class ZdZnodeIndexHandler(CommonBaseHandler):

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
        return self.render('config/znode/index.html',
                           clusters=clusters)


@route('/config/znode/displaytree')
class ZdZnodeShowHandler(CommonBaseHandler):

    """tree
    """
    args_list = [
        ArgsMap('cluster_name', required=True),
        ArgsMap('path', default="/"),
    ]

    @authenticated
    def response(self):
        """返回指定zookeeper集群的znode信息, 响应ajax请求
        """
        nodes = []
        normalized_path = normalize_path(self.path)

        if USE_QCONF:
            ZnodeService.get_znode_tree_from_qconf(self.cluster_name, normalized_path, nodes)
        else:
            zoo_client = ZookeeperService.get_zoo_client(self.cluster_name)
            if not zoo_client:
                return self.ajax_popup(code=300, msg="连接zookeeper出错！")
            ZnodeService.get_znode_tree(zoo_client, normalized_path, nodes)

        if normalized_path != "/" and len(nodes) <= 1:
            return self.ajax_popup(code=300, msg="对不起，该节点路径下（%s）无数据！" % self.path)

        znodes_data = json.dumps(nodes)
        return self.render('config/znode/displaytree.html',
                           cluster_name=self.cluster_name,
                           znodes_data=znodes_data)


@route(r'/config/znode/view')
class ZdZnodeViewHandler(CommonBaseHandler):
    '''view
    '''
    args_list = [
        ArgsMap('path', required=True),
        ArgsMap('cluster_name', required=True)
    ]

    @authenticated
    def response(self):
        """获取zookeeper节点的节点值
        """
        download_link = data = node_type = ""

        znode = ZdZnode.one(path=self.path, cluster_name=self.cluster_name, deleted="0")
        if znode:
            node_type = znode.type

        # 0代表普通节点，1代表文本节点
        if node_type == "1":
            download_link = "/config/znode/download?path={0}&cluster_name={1}".format(
                self.path, self.cluster_name)
        else:
            data = ZookeeperService.get(self.cluster_name, self.path)

        return self.render('config/znode/view.html',
                           data=data,
                           download_link=download_link)


@route(r'/config/znode/add', '新增')
class ZdZnodeAddHandler(CommonBaseHandler):

    '''add, 新增
    '''
    args_list = [
        ArgsMap('cluster_name', required=True),
        ArgsMap('parent_path', required=True),
    ]

    @authenticated
    def response(self):
        '''add
        '''
        return self.render('config/znode/add.html',
                           action='config/znode/save',
                           cluster_name=self.cluster_name,
                           parent_path=self.parent_path)


@route(r'/config/znode/edit', '修改')
class ZdZnodeEditHandler(CommonBaseHandler):

    """edit, 修改
    """
    args_list = [
        ArgsMap('cluster_name', required=True),
        ArgsMap('path', required=True),
    ]

    @authenticated
    def response(self):
        '''edit
        '''
        node_type = data = download_link = ""

        normalized_path = normalize_path(self.path)
        znode = ZdZnode.one(path=normalized_path, cluster_name=self.cluster_name, deleted='0')
        if znode:
            node_type = znode.type

        # "0"代表普通节点, "1"代表文本节点
        if node_type == "1":
            # 文件节点提供下载路径
            download_link = "/config/znode/download?path={0}&cluster_name={1}".format(
                self.path, self.cluster_name)

        else:
            data = ZookeeperService.get(self.cluster_name, self.path)

        return self.render('config/znode/edit.html',
                           action='/config/znode/save',
                           cluster_name=self.cluster_name,
                           path=normalized_path,
                           data=data,
                           download_link=download_link)


@route(r'/config/znode/batchedit', '批量增改')
class ZdZnodeEditTreeHandler(CommonBaseHandler):

    """batch edit, 批量修改
    """
    args_list = [
        ArgsMap('path', required=True),
        ArgsMap('cluster_name', required=True),
    ]

    @authenticated
    def response(self):
        '''batch edit
        '''
        child_znodes = ZnodeService.get_child_znodes(self.cluster_name, self.path)
        return self.render('config/znode/batchedit.html',
                           action='/config/znode/batchsave',
                           cluster_name=self.cluster_name,
                           parent_path=self.path,
                           child_znodes=child_znodes)


@route(r'/config/znode/syncstatus')
class ZdZnodeSyncstatusHandler(CommonBaseHandler):

    '''syncstatus
    '''
    args_list = [
        ArgsMap('cluster_name', required=True),
        ArgsMap('path', required=True)
    ]

    @authenticated
    def response(self):
        '''客户端同步状况查看
        '''
        # md5 value in zookeeper
        znode_value = ZookeeperService.get(self.cluster_name, self.path)
        znode_md5_value = hashlib.md5(znode_value).hexdigest()

        # agent value, idc转换为zookeeper集群名称，方便统一管理
        qconf_feedbacks = ZdQconfFeedback.select().where(
            (ZdQconfFeedback.idc == self.cluster_name) & (ZdQconfFeedback.path == self.path) &
            (ZdQconfFeedback.deleted == '0')
        )

        # check sync_status
        for feedback in qconf_feedbacks:
            # 只检查agent反馈记录中get_conf命令获取的值, 2代表get_conf命令的反馈记录
            if feedback.data_type != '2':
                continue
            if znode_md5_value == feedback.md5_value:
                feedback.sync_status = "已同步"
            else:
                feedback.sync_status = "未同步"

        return self.render('config/znode/syncstatus.html',
                           path=self.path,
                           idc=self.cluster_name,
                           feedbacks=qconf_feedbacks)


############################################################
# API for response
############################################################

@route(r'/config/znode/metainfo')
class ZdZnodeMetadataHandler(CommonBaseHandler):
    '''metainfo
    '''
    args_list = [
        ArgsMap('path', required=True),
        ArgsMap('cluster_name', required=True)
    ]

    @authenticated
    def response(self):
        """获取zookeeper节点的元数据信息
        """
        metainfo = dict()
        zk_node = ZdZnode.one(path=self.path, cluster_name=self.cluster_name)
        if zk_node:
            metainfo['type'] = zk_node.type
            metainfo['business'] = zk_node.business
        return json.dumps(metainfo)


@route(r'/config/znode/save')
class ZdZnodeSaveHandler(CommonBaseHandler):
    """save
    """
    args_list = [
        ArgsMap('cluster_name', required=True),
        ArgsMap('path', default=''),
        ArgsMap('parent_path', default=''),
        ArgsMap('node_name', default=''),
        ArgsMap('znode_type', default='0'),
        ArgsMap('data', default=''),
        ArgsMap('business', default=''),
    ]

    @authenticated
    def response(self):
        '''save
        '''
        # node_name中不可包含`/`特殊字符
        if self.node_name and not ZnodeService.is_node_name_ok(self.node_name):
            return self.ajax_popup(code=300, msg="节点名不允许包含特殊字符'/'！")

        zk_path = ""
        if not self.path:
            # 新增节点需要进行存在检验
            zk_path = os.path.join(self.parent_path, self.node_name)
            if ZookeeperService.exists(self.cluster_name, zk_path):
                return self.ajax_popup(code=300, msg="节点已经存在！")
        else:
            zk_path = self.path

        # znode_type, 0代表普通节点, 1代表文件节点
        zk_data = ""
        if self.znode_type == "1":
            if 'uploadfile' not in self.request.files:
                return self.ajax_popup(code=300, msg="请选择上传文件！")
            upload_file = self.request.files['uploadfile'][0]
            zk_data = upload_file['body']
        else:
            zk_data = self.data

        # 更新在zookeeper和mysql上存储的配置信息, 同时进行快照备份
        ZnodeService.set_znode(cluster_name=self.cluster_name,
                               path=zk_path,
                               data=zk_data,
                               znode_type=self.znode_type,
                               business=self.business)

        return self.ajax_ok(close_current=True)


@route(r'/config/znode/batchsave')
class ZdZnodeBatchSaveHandler(CommonBaseHandler):
    """save
    """
    args_list = [
        ArgsMap('cluster_name', required=True),
        ArgsMap('parent_path', required='/'),
        ArgsMap('business', default=''),
        ArgsMap('deleted', default=''),
    ]

    @authenticated
    def response(self):
        '''save
        '''
        keys = self.get_arguments("key")
        values = self.get_arguments("value")

        batch_data = []
        for node_name, node_value in zip(keys, values):
            # 过滤掉所有key为空字符串的项
            if node_name == '':
                continue
            # 检验node_name中是否包含`/`特殊字符
            if not ZnodeService.is_node_name_ok(node_name):
                return self.ajax_popup(code=300, msg="节点名不允许包含特殊字符'/'！")
            batch_data.append((node_name, node_value))

        # 更新字典，需要删除旧字典与新字典的差集项
        ZnodeService.delete_znodes_diff_with_keys(self.cluster_name, self.parent_path, keys)
        # 更新在zookeeper和mysql上存储的配置信息, 同时进行快照备份
        ZnodeService.set_batch_znodes(cluster_name=self.cluster_name,
                                      parent_path=self.parent_path,
                                      batch_data=batch_data,
                                      business=self.business)

        return self.ajax_ok(close_current=True)


@route(r'/config/znode/delete', '删除')
class ZdZnodeDeleteHandler(CommonBaseHandler):

    """delete, 删除
    """
    args_list = [
        ArgsMap('cluster_name', required=True),
        ArgsMap('path', required=True),
        ArgsMap('recursive', default="0"),
    ]

    @authenticated
    def response(self):
        '''delete
        '''
        # recursive or not
        recursive = self.recursive == "1"
        try:
            # 删除节点在mysql上的数据信息
            ZnodeService.delete_znodes(self.cluster_name, self.path, recursive, del_snapshots=False)
            ZookeeperService.delete(self.cluster_name, self.path, recursive)
            return self.ajax_ok(close_current=False)
        except (NotEmptyError, BadArgumentsError) as exc:
            return self.ajax_popup(code=300, msg="无法删除节点！")


@route(r'/config/znode/download', '下载')
class ZdZnodeDownloadHandler(CommonBaseHandler):

    """download
    """
    args_list = [
        ArgsMap('path', required=True),
        ArgsMap('cluster_name', required=True),
    ]

    @authenticated
    def response(self):
        """download
        """
        data = ZookeeperService.get(self.cluster_name, self.path)
        filename = "{}".format(self.path.rsplit('/')[-1])
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename={}'.format(filename))
        self.finish(data)


@route(r'/config/znode/export', '导出')
class ZdZnodeExportHandler(CommonBaseHandler):

    """export,导出数据到文件
    """
    args_list = [
        ArgsMap('path', required=True),
        ArgsMap('cluster_name', required=True),
    ]

    @authenticated
    def response(self):
        '''导出数据到文件中
        '''
        data = ZookeeperService.get(self.cluster_name, self.path)
        filename = "{}".format(self.path.rsplit('/')[-1])
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename={}'.format(filename))
        self.finish(data)
