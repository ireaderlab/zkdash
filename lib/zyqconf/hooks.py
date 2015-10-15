#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Copyright (c) 2014,掌阅科技
All rights reserved.

摘    要: hooks.py
创 建 者: zhuangshixiong
创建日期: 2015-09-22
'''
# pylint: disable=invalid-name, missing-docstring
from collections import defaultdict


class Hook(object):
    """
    A single hook that can be listened for.
    """
    def __init__(self):
        self.subscribers = []

    def attach(self, task):
        """attach a task to this hook.
        """
        self.subscribers.append(task)

    def detach(self, task):
        """detach a task from this hook
        """
        self.subscribers.remove(task)

    def send(self, **kwargs):
        """send msg to tasks and return their results.
        """
        return [task(**kwargs) for task in self.subscribers]


_HOOKS = defaultdict(Hook)


def all_hooks():
    """
    Return all registered hooks.
    """
    return _HOOKS


def get_hook(name):
    """
    Return hook with given name, creating it if necessary.
    """
    return _HOOKS[name]


def on(name):
    """Return a decorator that attach the wrapped function to the hook with given name.
    """
    hook = get_hook(name)

    def hook_decorator(func):
        hook.attach(func)
        return func
    return hook_decorator
