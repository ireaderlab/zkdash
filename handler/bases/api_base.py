#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Copyright (c) 2014,掌阅科技
All rights reserved.

摘    要: api_base.py
创 建 者: ZengDuju
创建日期: 2015-04-10
'''
from handler.bases import CommonBaseHandler


class ApiBaseHandler(CommonBaseHandler):
    """ApiBaseHandler 不进行XSRF cookie检查
    """

    def check_xsrf_cookie(self):
        """重写check_xsrf_cookie
        """
        pass
