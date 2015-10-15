#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=unused-argument

"""
Copyright (c) 2014,掌阅科技
All rights reserved.

摘    要: common_base.py
创 建 者: warship
创建日期: 2015-10-09
"""
from handler.bases import RestHandler


class CommonBaseHandler(RestHandler):

    """提供各个模块公用的业务处理逻辑
    """

    def parse_query(self, model):
        '''解析查询条件
        Args:
            column: 列名
            operator: 操作
            query: 查询值
        '''
        column = self.get_arguments('column') or self.get_arguments('column[]')
        operator = self.get_arguments('operator') or self.get_arguments('operator[]')
        query = self.get_arguments('query') or self.get_arguments('query[]')
        clauses = []
        for i, q in enumerate(query):
            if not q:
                continue
            model_column = getattr(model, column[i])
            op = operator[i]
            if op == '=':
                clause = (model_column == q)
            elif op == '>':
                clause = (model_column > q)
            elif op == '>=':
                clause = (model_column >= q)
            elif op == '<':
                clause = (model_column < q)
            elif op == '<=':
                clause = (model_column <= q)
            else:
                if column[i] == 'id':
                    # 对id做特殊处理，不支持like操作
                    clause = (model_column == q)
                else:
                    clause = (model_column ** "{}%".format(q))
            clauses.append(clause)
        if hasattr(model, 'deleted'):
            clauses.append(getattr(model, 'deleted') == '0')
        elif hasattr(model, 'disable'):
            clauses.append(getattr(model, 'disable') == '0')
        clauses.append(getattr(model, 'id') >= 0)
        return clauses

    @staticmethod
    def ajax_ok(forward='', forward_confirm='', close_current=True):
        '''响应bjui ok的状态
        '''
        res = {
            'statusCode': '200',
            'message': '成功',
            'tabid': '_' + forward.replace('/', '_'),
            'closeCurrent': close_current,
            'forward': forward,
            'forwardConfirm': forward_confirm
        }
        return res

    @staticmethod
    def ajax_timeout(forward='', forward_confirm='', close_current=False):
        '''响应bjui超时状态
        '''
        res = {
            "statusCode": "301",
            "message": "会话超时",
            "closeCurrent": close_current,
            "forward": forward,
            "forwardConfirm": forward_confirm
        }
        return res

    @staticmethod
    def ajax_dialog_ok(forward='', forward_confirm='', close_current=False):
        '''响应对话框 OK
        '''
        res = {
            "statusCode": "200",
            "message": "成功",
            "tabid": "",
            "dialogid": "dialog-mask",
            "closeCurrent": close_current,
            "forward": forward,
            "forwardConfirm": forward_confirm
        }
        return res

    @staticmethod
    def ajax_popup(forward='', forward_confirm='', close_current=False, code='', msg=''):
        '''信息提示
        '''
        res = {
            'statusCode': code,
            'message': msg,
            'closeCurrent': close_current,
            'forward': forward,
            'forwardConfirm': forward_confirm
        }
        return res
