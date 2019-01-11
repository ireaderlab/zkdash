#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Copyright (c) 2014,掌阅科技
All rights reserved.

摘    要: __init__.py
创 建 者: zhuangshixiong
创建日期: 2015-09-09
'''
# pylint: disable=relative-import
import ctypes
import hooks
from .types import (
    QconfNode,
    ListNode,
    DictNode,
    HOOK_CONF_ERROR,
)
qconf_py = ctypes.CDLL('./qconf_py.so')

__version__ = '1.0.0'

__all__ = [
    'qconf_py',
    'hooks',
    'QconfNode',
    'DictNode',
    'ListNode',
    'HOOK_CONF_ERROR',
]
