#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014,掌阅科技
All rights reserved.

摘    要: paginate.py
创 建 者: WangLichao
创建日期: 2015-02-06
"""
# pylint: disable=arguments-differ
from tornado.web import UIModule


class Paginate(UIModule):

    '''分页组件
    '''

    def render(self, total, current_page, page_size):
        '''
        Args:
            total: 总数
            current_page: 当前页
            page_size: 页码数
        '''
        return self.render_string("uimodule/paginate.html",
                                  total=total,
                                  current_page=current_page,
                                  page_size=page_size)
