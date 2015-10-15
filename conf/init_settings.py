#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Copyright (c) 2013,掌阅科技
All rights reserved.

File Name: init_settings.py
Author: zhuangshixiong
Created on: 2015-10-15
'''
import os
import sys
import imp

import yaml
import tornado
from tornado.options import define, options

define("port", default=8080, help="port to listen", type=int)
define("debug", default=True, help="debug mode or not")

tornado.options.parse_command_line()

if options.debug:
    import tornado.autoreload


def create_settings_module(file_name):
    """ create settings module from config file
    """
    conf_data = None
    with open(file_name, 'r') as conf_file:
        conf_data = yaml.load(conf_file)
        if not isinstance(conf_data, dict):
            raise Exception("config file not parsed correctly")

    module = imp.new_module('settings')
    module.__dict__.update(conf_data)
    module.__dict__.update({'OPTIONS': options})
    return module


# 根据配置文件生成配置模块，供全局使用
settings_module = create_settings_module('{}/conf/conf.yml'.format(os.getcwd()))
sys.modules['conf.settings'] = settings_module
