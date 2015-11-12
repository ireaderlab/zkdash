#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014,掌阅科技
All rights reserved.

摘    要: base.py
创 建 者: WangLichao
创建日期: 2014-12-5
"""
import time
import json

from tornado import escape
from tornado.web import RequestHandler

from lib.utils import toint, tofloat
from lib.utils import log_format
from conf import log


class ArgsMap(object):

    """请求参数对象类封装
    """
    __slots__ = ("attribute", "argument", "default", "required", "refresh")

    def __init__(self, argument, attribute=None, default=None, required=False, refresh=False):
        self.argument = argument
        if attribute is None:
            self.attribute = argument
        else:
            self.attribute = attribute
        self.default = default
        self.refresh = refresh
        # default值用做错误参数返回的时候required=True
        self.required = required

    def __str__(self):
        """
        """
        return "argument:{}, default:{}, required:{}!".format(
            self.argument,
            self.default,
            self.required,
        )


class BaseHandler(RequestHandler):

    """基础类封装
    """
    SUPPORTED_METHODS = ("GET", "POST")

    def __init__(self, *argc, **argkw):
        super(BaseHandler, self).__init__(*argc, **argkw)

    def get_current_user(self):
        '''获取当前用户
        '''
        return "tokyo"

    def prepare(self):
        '''get/post前处理函数
        '''
        self.target_tab = self.get_argument('target_tab', '')

    def get_xsrf(self):
        '''获取签名值
        '''
        return escape.xhtml_escape(self.xsrf_token)


class RestHandler(BaseHandler):

    """RESTful接口基类
    """
    args_list = []

    def initialize(self):
        """初始化相关属性
        """
        self._start_time = time.time()  # 接口实例开始时间

    def _args_set(self):
        """handler参数属性设置
        """
        for args_map in self.args_list:
            try:
                val = self.get_argument(args_map.argument, args_map.default)
                if val == '':
                    val = args_map.default
                if isinstance(val, unicode):
                    val = val.encode('utf8')
                if isinstance(args_map.default, int):
                    val = toint(val)
                if isinstance(args_map.default, float):
                    val = tofloat(val)
            except ValueError:
                raise ValueError('{} 参数传递有误!'.format(args_map.argument))
            if args_map.required:
                if val == args_map.default:
                    raise ValueError('{} 参数为必填参数!'.format(args_map.argument))
            setattr(self, args_map.attribute, val)
        setattr(self, 'refresh', int(self.get_argument('refresh', 0)))

    def get(self):
        """get协议,获取接口参数
        """
        return self._exec()

    def post(self):
        """post协议，获取接口参数
        """
        return self._exec()

    def _exec(self):
        '''with退出处理
        '''
        try:
            self._args_set()
        except ValueError as e:
            log_format(self, error_info=e)
            msg = "参数错误，请检查参数后再请求! {}".format(e)
            return self.send_obj({'status': 1000, 'msg': msg})
        try:
            res = self.response()
        except Exception:
            import traceback
            e = traceback.format_exc()
            log.error('Internal Error: %s', e)
            return self.send_obj({'status': 10001, 'msg': str(e)})
        if not self._finished:
            return self.send_obj(res)

    def response(self):
        """不同接口进行重写
        """
        return None

    def send_obj(self, obj):
        """输出json格式数据
        Args:
            obj: 输出的对象
        """
        if not obj:
            error_info = {
                'status': 1,
                'msg': '获取接口信息失败!\t{}'.format('\t'.join(str(am) for am in self.args_list)),
            }
            obj = error_info
        self.set_header('Content-Type', 'application/json; charset=utf-8')
        self.write(json.dumps(obj))
