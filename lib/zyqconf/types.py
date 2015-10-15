#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Copyright (c) 2015,掌阅科技
All rights reserved.

File Name: types.py
Author: zhuangshixiong
Created on: 2015-09-09
'''
# pylint: disable=missing-docstring
import os
import traceback
import logging
import yaml
from . import qconf_py
from . import hooks

# zookeeper节点上存储字典和列表数据结构所使用的特殊节点值
DICT_SYMBOL = "DICT_ZNODE"
LIST_SYMBOL = "LIST_ZNODE"

# 获取配置失败时的钩子名称
HOOK_CONF_ERROR = "zyqconf.conf_error"

# Set default logging handler to avoid "No handlers could be found
# for logger" warning, taken from peewee
try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logger = logging.getLogger('zyqconf')
logger.addHandler(NullHandler())


def deserialize(data):
    """反序列化zookeeper节点数据
    """
    return yaml.load(data)


def serialize(data):
    """序列化zookeeper节点数据
    """
    return yaml.dump(data)


def quote_key(key):
    """特殊字符'/'转义处理
    """
    return key.replace('/', '%2F')


def unquote_key(key):
    """特殊字符'/'反转义处理
    """
    return key.replace('%2F', '/')


class QconfNode(object):
    """Zookeeper节点的基础封装
    """

    def __init__(self, parent_path):
        self.parent_path = parent_path

    def __getattr__(self, key):
        """重载点运算符
        """
        # 忽略python中的魔术属性
        if key.startswith("__"):
            return
        path = self.join_path(self.parent_path, key)
        return self.get_conf(path)

    def join_path(self, path_name, file_name):
        """拼接节点路径，转义字符'/'需要特殊处理，避免zookeeper产生歧义
        """
        file_name = quote_key(file_name)
        return os.path.join(path_name, file_name)

    def get_conf(self, path):
        """通过qconf获取给定路径的节点数据
        """
        conf = None
        try:
            value = qconf_py.get_conf(path)
            # 反序列化
            value = deserialize(value)
        except qconf_py.Error:
            exc_info = "could not get conf from path: {0}\n{1}".format(path, traceback.format_exc())
            logger.warning(exc_info)
            # 钩子，发布消息
            hooks.get_hook(HOOK_CONF_ERROR).send(path=path, exc_info=exc_info)
        else:
            if value == DICT_SYMBOL:
                conf = DictNode(path)
            elif value == LIST_SYMBOL:
                conf = ListNode(path)
            else:
                conf = value
        return conf


class ListNode(QconfNode):
    """在Zookeeper普通节点上模拟出python列表(list)常用方法
    """

    def __init__(self, path):
        super(ListNode, self).__init__(path)

    def __getitem__(self, index):
        path = self.join_path(self.parent_path, str(index))
        item = self.get_conf(path)
        if item is None:
            raise IndexError
        return item

    def __len__(self):
        keys = qconf_py.get_batch_keys(self.parent_path)
        return len(keys)

    def __iter__(self):
        """迭代器协议实现
        """
        keys = qconf_py.get_batch_keys(self.parent_path)
        for key in keys:
            path = self.join_path(self.parent_path, key)
            yield self.get_conf(path)

    def __repr__(self):
        list_repr = []
        keys = qconf_py.get_batch_keys(self.parent_path)
        for key in sorted(keys):
            list_repr.append(self[key])
        return repr(list_repr)

    def as_list(self):
        """递归获取列表所有数据
        """
        list_obj = []
        keys = qconf_py.get_batch_keys(self.parent_path)
        for key in sorted(keys):
            path = self.join_path(self.parent_path, key)
            value = node = self.get_conf(path)
            if isinstance(node, DictNode):
                value = node.as_dict()
            elif isinstance(node, ListNode):
                value = node.as_list()
            list_obj.append(value)
        return list_obj


class DictNode(QconfNode):
    """在Zookeeper普通节点上模拟出python字典(dict)常用方法
    """

    def __init__(self, path):
        super(DictNode, self).__init__(path)

    def __getitem__(self, key):
        path = self.join_path(self.parent_path, str(key))
        item = self.get_conf(path)
        if item is None:
            raise KeyError(key)
        return item

    def __iter__(self):
        keys = qconf_py.get_batch_keys(self.parent_path)
        for key in keys:
            yield unquote_key(key)

    def __len__(self):
        keys = qconf_py.get_batch_keys(self.parent_path)
        return len(keys)

    def __eq__(self, dict_obj):
        if len(self) != len(dict_obj):
            return False
        for key, value in dict_obj.iteritems():
            if key not in self or self[key] != value:
                return False
        return True

    def __contains__(self, key):
        keys = self.keys()
        return key in keys

    def __repr__(self):
        dict_repr = {}
        keys = qconf_py.get_batch_keys(self.parent_path)
        for key in keys:
            path = self.join_path(self.parent_path, key)
            dict_repr[key] = self.get_conf(path)
        return repr(dict_repr)

    def get(self, key, default=None):
        if key in self.keys():
            return self[key]
        else:
            return default

    def keys(self):
        keys = qconf_py.get_batch_keys(self.parent_path)
        return [unquote_key(key) for key in keys]

    def items(self):
        items = []
        keys = qconf_py.get_batch_keys(self.parent_path)
        for key in keys:
            path = self.join_path(self.parent_path, key)
            items.append((key, self.get_conf(path)))
        return items

    def iteritems(self):
        keys = qconf_py.get_batch_keys(self.parent_path)
        for key in keys:
            path = self.join_path(self.parent_path, key)
            yield (key, self.get_conf(path))

    def itervalues(self):
        keys = qconf_py.get_batch_keys(self.parent_path)
        for key in keys:
            path = self.join_path(self.parent_path, key)
            yield self.get_conf(path)

    def as_dict(self):
        """递归获取字典所有数据
        """
        dict_obj = {}
        keys = qconf_py.get_batch_keys(self.parent_path)
        for key in keys:
            path = self.join_path(self.parent_path, key)
            value = node = self.get_conf(path)
            if isinstance(node, DictNode):
                value = node.as_dict()
            elif isinstance(node, ListNode):
                value = node.as_list()
            dict_obj[key] = value
        return dict_obj
