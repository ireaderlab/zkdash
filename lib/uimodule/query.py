#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2015,掌阅科技
All rights reserved.

摘    要: query.py
创 建 者: WangLichao
创建日期: 2015-03-06
"""
# pylint: disable=arguments-differ
from tornado.web import UIModule

OPERATOR = {
    'like': '包含',
    '=': '等于',
    '!=': '不等于',
    '>': '大于',
    '>=': '大于等于',
    '<': '小于',
    '<=': '小于等于',
}


class Query(UIModule):

    '''操作条件
    '''

    def render(self, column, default_column,
               default_operator, time_flag=False):
        '''
        Args:
            column: 数据库列字典
            default_column: 默认列
            operator: 操作字典
            default_operator: 默认操作
            time_flag: 输入为时间字段标记
        '''
        return self.render_string("uimodule/query.html",
                                  column=column,
                                  default_column=default_column,
                                  default_operator=default_operator,
                                  operator=OPERATOR,
                                  time_flag=time_flag)
