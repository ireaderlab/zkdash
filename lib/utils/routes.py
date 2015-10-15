#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014,MagickCode
All rights reserved.

摘    要: routes.py
创 建 者: WangLichao
创建日期: 2014-08-07
"""

import os
import tornado.web

from conf import log


class Route(object):

    """修饰RequestHandlers 并且构造handler的url路由配置list
    每次@route('...')被调用,都将自动添加配置的路径的路由URI到list中
    并提供了重定向功能
    Example
    -------
    @route('/some/path')
    class SomeRequestHandler(RequestHandler):
        def get(self):
            goto = self.reverse_url('other')
            self.redirect(goto)

    @route('/some/other/path', name='other')
    class SomeOtherRequestHandler(RequestHandler):
        def get(self):
            goto = self.reverse_url('SomeRequestHandler')
            self.redirect(goto)

    my_routes = route.get_routes()
    """

    _routes = []

    def __init__(self, uri, name=None, attr=None):
        self._uri = uri
        self.name = name
        self.attr = attr

    def __call__(self, handler):
        """如果类中有该修饰器，则该函数会被调用
        Args:
            handler: tornado.web.RequestHandler对象
        """
        module_name = handler.__module__
        real_uri = self.dir_to_uri(module_name)
        self._routes.append(tornado.web.url(real_uri, handler, name=handler.__name__))
        return handler

    def dir_to_uri(self, module_name):
        """将路径转换为uri
        Args:
            module_name: 路径名称
        """
        assert self._uri.startswith('/'), "URI must startswith '/'"
        log.info('request uri auto generate: {} ---> {}'.format(module_name, self._uri))
        return self._uri

    @classmethod
    def get_routes(cls):
        """获取路由
        """
        return cls._routes


def route_redirect(from_, to_, name=None):
    """重定向
    >>> from routes import route, route_redirect
    >>> route_redirect('/smartphone$', '/smartphone/')
    >>> route_redirect('/iphone/$', '/smartphone/iphone/', name='iphone_shortcut')
    >>> @route('/smartphone/$')
    >>> class SmartphoneHandler(RequestHandler):
    >>>      def get(self):
    >>>          ...
    """
    Route.get_routes.append(tornado.web.url(from_,
                                            tornado.web.RedirectHandler,
                                            dict(url=to_),
                                            name=name))


def load(package_name):
    """加载目录
    """
    import pkgutil
    import sys

    __import__(package_name)
    controllers_module = sys.modules[package_name]

    # prefix = controllers_module.__name__ + "."

    # 支持子模块
    path = os.path.abspath(controllers_module.__path__[0])
    root_length = len(os.path.dirname(path) + '/')
    for root_dirs_files in os.walk(path):
        module_root = root_dirs_files[0]
        module_prefix = module_root[root_length:].replace(os.sep, '.') + '.'
        for importer_modname_ispkg in pkgutil.iter_modules([module_root], module_prefix):
            modname = importer_modname_ispkg[1]
            __import__(modname)

    # 通过修饰器获取路由配置
    url_routes = Route.get_routes()
    return url_routes

if __name__ == '__main__':
    pass
