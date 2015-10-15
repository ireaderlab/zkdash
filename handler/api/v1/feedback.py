#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014,掌阅科技
All rights reserved.

摘    要: feedback.py
创 建 者: zhuangshixiong
创建日期: 2015-06-24
"""
from datetime import datetime

from handler.bases import ApiBaseHandler
from handler.bases import ArgsMap
from lib import route
from model.db.zd_qconf_feedback import ZdQconfFeedback


@route(r'/api/v1/feedback')
class ZdQconfFeedbackSaveHandler(ApiBaseHandler):
    """save
    """
    args_list = [
        ArgsMap('id', default=''),
        ArgsMap('hostname', default=''),
        ArgsMap('ip', default=''),
        ArgsMap('node_whole', default=''),
        ArgsMap('value_md5', default=''),
        ArgsMap('idc', default=''),
        ArgsMap('update_time', default=''),
        ArgsMap('data_type', default=''),
        ArgsMap('deleted', default=''),
    ]

    def response(self):
        '''add
        '''
        feedback = ZdQconfFeedback.one(idc=self.idc, ip=self.ip, path=self.node_whole)
        if feedback is None:
            # create new feedback record
            feedback = ZdQconfFeedback()
        # 填充字段
        if self.idc:
            feedback.idc = self.idc
        if self.ip:
            feedback.ip = self.ip
        if self.hostname:
            feedback.hostname = self.hostname
        if self.node_whole:
            feedback.path = self.node_whole
        if self.value_md5:
            feedback.md5_value = self.value_md5
        if self.update_time:
            # convert unix timestamp to datetime
            update_time = datetime.fromtimestamp(
                int(self.update_time)).strftime('%Y-%m-%d %H:%M:%S')
            feedback.update_time = update_time
        if self.data_type:
            feedback.data_type = self.data_type
        # 自定义字段
        if self.deleted:
            feedback.deleted = self.deleted
        feedback.save()
        # qconf protocol, return '0' means ok
        self.finish('0')
