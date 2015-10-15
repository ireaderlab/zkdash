#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014,掌阅科技
All rights reserved.

摘    要: 部分工具方法
创 建 者: WangLichao
创建日期: 2014-12-3
"""
import time
import inspect
import sys

from conf import log


def toint(value, default=0):
    """转成 int 类别，避免异常
    """
    if not value:
        return default
    return int(value)


def tofloat(value, default=0.0):
    """转成 float 类别，避免异常
    """
    if not value:
        return default
    return float(value)


def normalize_path(path):
    """normalize path
    """
    path = path.strip('/')
    return '/' + path


def page_range(record_number, page_size, current_page):
    """计算分页时元索的区间以偏移量start 和 stop
    Args:
        record_number: 记录数
        page_size: 每页记录数
        current_page: 当前页
    Returns:
        分页的开始位置与结束位置
    """
    if current_page < 1:
        current_page = 1
    start = 0 if current_page == 1 else (current_page - 1) * page_size
    end = current_page * page_size - 1
    end = end if end < record_number else record_number - 1
    return (start, end)


def page_compute(record_number, page_size, current_page):
    """计算总页数和有效的当前页
    Args:
        record_number: 记录数
        page_size: 每页记录数
        current_page: 当前页
    """
    current_page = max(current_page, 1)
    page_total = (record_number + page_size - 1) / page_size
    current_page = min(current_page, page_total)
    return (current_page, page_total)


def log_format(instance, func_name=None, params=None, error_info=None):
    """格式化log信息
    Args:
        instance: 类实例,当前业务环境下针对Handler类
        func_name: 类中调用返回为空的方法
        params: str 需要在log中说明的参数
        error_info: error级log的错误信息
    """
    if inspect.isclass(type(instance)):
        module_name = instance.__module__
        class_name = instance.__class__.__name__
        if not params:
            params = instance.request.uri
        end_time = time.time()
        spend_time = round((end_time - instance._start_time) * 1000, 2)
        if error_info:
            log.error('%s.%s faild spend_time:%sms params:(%s) error info:%s',
                      module_name,
                      class_name,
                      spend_time,
                      params,
                      error_info)
            return
        if func_name:
            log.warning('%s.%s call %s faild spend_time:%sms params:(%s)',
                        module_name,
                        class_name,
                        func_name,
                        spend_time,
                        params)
        else:
            log.warning('%s.%s faild spend_time:%sms params:(%s)',
                        module_name,
                        class_name,
                        spend_time,
                        params)


def load_class(s):
    '''获取文件模块中的类对象
    '''
    path, klass = s.rsplit('.', 1)
    __import__(path)
    mod = sys.modules[path]
    return getattr(mod, klass)


def find_subclasses(klass, include_self=False):
    """find all subclasses
    """
    subclasses = []
    for subclass in klass.__subclasses__():
        subclasses.extend(find_subclasses(subclass, True))
    if include_self:
        subclasses.append(klass)
    return subclasses
