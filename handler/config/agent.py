#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014,掌阅科技
All rights reserved.

摘    要: agent.py
创 建 者: zhuangshixiong
创建日期: 2015-08-26
"""
import urllib
import operator
import json
from difflib import Differ
from tornado.web import authenticated
from peewee import OperationalError
from kazoo.exceptions import NoNodeError

from handler.bases import CommonBaseHandler
from handler.bases import ArgsMap
from lib import route
from lib.excel import ExcelWorkBook
from model.db.zd_qconf_agent import ZdQconfAgent
from model.db.zd_zookeeper import ZdZookeeper
from service import zookeeper as ZookeeperService
from conf import log


@route(r'/config/agent/index', '查看')
class ZdQconfAgentIndexHandler(CommonBaseHandler):

    '''index, 查看
    '''
    args_list = [
        ArgsMap('pageSize', 'page_size', default=30),
        ArgsMap('pageCurrent', 'current_page', default=1),
        ArgsMap('orderDirection', 'order_direction', default="asc"),
        ArgsMap('orderField', 'order_field', default="id"),
    ]

    @authenticated
    def response(self):
        '''index
        '''
        clauses = self.parse_query(ZdQconfAgent)
        order = getattr(ZdQconfAgent, self.order_field)
        records = ZdQconfAgent.select().order_by(
            getattr(order, self.order_direction)()
        ).where(reduce(operator.and_, clauses))
        self.render('config/agent/index.html',
                    action='/config/agent/index',
                    total=records.count(),
                    current_page=self.current_page,
                    page_size=self.page_size,
                    records=records.paginate(self.current_page, self.page_size))


@route(r'/config/agent/watch', '观察')
class WsAgentWatchHandler(CommonBaseHandler):

    '''watch, 观察
    '''
    args_list = [
        ArgsMap('agent_register_prefix', default="/qconf/__qconf_register_hosts")
    ]

    @authenticated
    def response(self):
        '''watch
        '''
        clusters = ZdZookeeper.select().where(ZdZookeeper.deleted == "0")
        self.render('config/agent/watch.html',
                    clusters=clusters,
                    agent_register_prefix=self.agent_register_prefix)


@route(r'/config/agent/checkagents', '检查agents')
class WsAgentCheckAgentsHandler(CommonBaseHandler):

    '''check agents
    '''
    args_list = [
        ArgsMap('cluster_name', required=True),
        ArgsMap('agent_register_prefix', default="/qconf/__qconf_register_hosts")
    ]

    @authenticated
    def response(self):
        '''watch
        '''
        zoo_client = ZookeeperService.get_zoo_client(self.cluster_name)
        if not zoo_client:
            return self.ajax_popup(code=300, msg="连接zookeeper出错！")

        try:
            zk_agents = zoo_client.get_children(self.agent_register_prefix)
        except NoNodeError:
            return self.ajax_popup(code=300, msg="节点路径不存在！")

        records = ZdQconfAgent.select().where(
            (ZdQconfAgent.cluster_name == self.cluster_name) &
            (ZdQconfAgent.deleted == '0')
        )
        mysql_agents = [record.hostname for record in records]

        # agent在mysql上的统计信息和在zookeeper上注册信息的对比
        agents_stat = []
        for diff_info in Differ().compare(mysql_agents, zk_agents):
            agent_name = diff_info[2:]
            if diff_info[0] == "+":
                cmp_res = ['无', agent_name]
            elif diff_info[0] == "-":
                cmp_res = [agent_name, '无']
            else:
                cmp_res = [agent_name, agent_name]
            agents_stat.append(cmp_res)
        return agents_stat


@route(r'/config/agent/search')
class ZdQconfAgentSearchHandler(CommonBaseHandler):

    '''search,搜索
    '''
    args_list = [
        ArgsMap('pageSize', 'page_size', default=30),
        ArgsMap('pageCurrent', 'current_page', default=1),
        ArgsMap('orderDirection', 'order_direction', default="asc"),
        ArgsMap('orderField', 'order_field', default="id"),
    ]

    @authenticated
    def response(self):
        '''search
        '''
        clauses = self.parse_query(ZdQconfAgent)
        order = getattr(ZdQconfAgent, self.order_field)
        records = ZdQconfAgent.select().order_by(
            getattr(order, self.order_direction)()
        ).where(reduce(operator.and_, clauses))
        self.render('config/agent/datagrid.html',
                    total=records.count(),
                    current_page=self.current_page,
                    page_size=self.page_size,
                    records=records.paginate(self.current_page, self.page_size))


@route(r'/config/agent/save')
class ZdQconfAgentSaveHandler(CommonBaseHandler):
    """save
    """
    args_list = [
        ArgsMap('id', default=''),
        ArgsMap('ip', default=''),
        ArgsMap('hostname', default=''),
        ArgsMap('cluster_name', default=''),
        ArgsMap('notes', default=''),
        ArgsMap('create_user', default=''),
        ArgsMap('create_time', default=''),
        ArgsMap('update_user', default=''),
        ArgsMap('update_time', default=''),
        ArgsMap('deleted', default=''),
    ]

    @authenticated
    def response(self):
        '''add
        '''
        if self.id:
            # 修改记录
            tb_inst = ZdQconfAgent.one(id=self.id)
        else:
            # 新增记录
            tb_inst = ZdQconfAgent()
        if self.id:
            tb_inst.id = self.id
        if self.ip:
            tb_inst.ip = self.ip
        if self.hostname:
            tb_inst.hostname = self.hostname
        if self.cluster_name:
            tb_inst.cluster_name = self.cluster_name
        if self.notes:
            tb_inst.notes = self.notes
        if self.create_user:
            tb_inst.create_user = self.create_user
        if self.create_time:
            tb_inst.create_time = self.create_time
        if self.update_user:
            tb_inst.update_user = self.update_user
        if self.update_time:
            tb_inst.update_time = self.update_time
        if self.deleted:
            tb_inst.deleted = self.deleted
        tb_inst.save()
        return self.ajax_ok(forward="/config/agent/index")


@route(r'/config/agent/add', '新增')
class ZdQconfAgentAddHandler(CommonBaseHandler):

    '''add, 新增
    '''

    @authenticated
    def response(self):
        '''add
        '''
        clusters = ZdZookeeper.select().where(ZdZookeeper.deleted == "0")
        return self.render('config/agent/add.html',
                           action='config/agent/save',
                           clusters=clusters)


@route(r'/config/agent/edit', '修改')
class ZdQconfAgentEditHandler(CommonBaseHandler):

    """edit, 修改
    """
    args_list = [
        ArgsMap('info_ids', default=''),
    ]

    def response(self):
        '''edit
        '''
        if self.info_ids:
            id_li = self.info_ids.split(',')
            if len(id_li) != 1:
                return self.ajax_popup(close_current=False, code=300, msg="请选择单条记录进行修改")
            clusters = ZdZookeeper.select().where(ZdZookeeper.deleted == "0")
            record = ZdQconfAgent.one(id=id_li[0])
            return self.render('config/agent/edit.html',
                               action='/config/agent/save',
                               clusters=clusters,
                               record=record)
        else:
            return self.ajax_popup(close_current=False, code=300, msg="请选择某条记录进行修改")


@route(r'/config/agent/delete', '删除')
class ZdQconfAgentDeleteHandler(CommonBaseHandler):

    """delete, 删除
    """
    args_list = [
        ArgsMap('info_ids', default=''),
    ]

    def response(self):
        '''delete
        '''
        if not self.info_ids:
            return self.ajax_popup(close_current=False, code=300, msg="请选择某条记录进行删除")

        id_list = self.info_ids.split(',')
        try:
            del_query = ZdQconfAgent.delete().where(ZdQconfAgent.id << id_list)
            del_query.execute()
        except OperationalError as exc:
            log.error("error occurred while delete agents, ids: %s\n%s", id_list, str(exc))
            return self.ajax_popup(close_current=False, code=300, msg="删除失败！")
        return self.ajax_ok(close_current=False)


@route(r'/config/agent/export', '导出')
class ZdQconfAgentExportHandler(CommonBaseHandler):

    """export,导出数据到excel
    """
    args_list = [
        ArgsMap('info_ids', default=''),
    ]

    def response(self):
        '''导出选中数据到excel中
        '''
        id_li = self.info_ids.split(',')
        sheet_text = ZdQconfAgent.select().where(ZdQconfAgent.id << id_li)
        sheet_title = [
            {'name': 'ip'},
            {'name': '主机名'},
            {'name': '说明'},
        ]
        bind_attr = (
            'ip',
            'hostname',
            'notes',
        )
        ewb = ExcelWorkBook()
        sheet_name = ZdQconfAgent._meta.db_table
        ewb.add_sheet(sheet_name)
        ewb.add_title(sheet_name, sheet_title)
        ewb.add_text(sheet_name, sheet_text, bind=bind_attr)
        filename = '{}.xls'.format(sheet_name)
        filename = urllib.urlencode({'filename': filename})
        self.set_header('Content-Disposition', 'attachment;{}'.format(filename))
        self.finish(ewb.get_stream())
