#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Copyright (c) 2013,掌阅科技
All rights reserved.

File Name: logger.py
Author: WangLichao
Created on: 2014-03-28
'''
import os
import os.path
import logging
import logging.handlers
LOGGER_LEVEL = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}


def init_logger(log_conf_items, suffix=None, log_name=None):
    """
    初始化logger.
    Args:
      log_conf_items: 配置项list.
    """
    logger = logging.getLogger(log_name)
    for log_item in log_conf_items:
        path = os.path.expanduser(log_item['file'])
        if suffix:
            path = '%s.%s' % (path, suffix)
        dir_name = os.path.dirname(path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)
        handler = logging.handlers.TimedRotatingFileHandler(
            path,
            when=log_item['when'],
            interval=int(log_item['interval']),
            backupCount=int(log_item['backup_count']),
        )
        enable_levels = [LOGGER_LEVEL[i] for i in log_item['log_levels']]
        handler.addFilter(LevelFilter(enable_levels, False))
        handler.suffix = log_item['backup_suffix']
        formatter = logging.Formatter(log_item['format'])
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(log_item['level'])


class LevelFilter(logging.Filter):

    '''日志过滤器
    '''

    def __init__(self, passlevels, reject):
        super(LevelFilter, self).__init__()
        self.passlevels = passlevels
        self.reject = reject

    def filter(self, record):
        if self.reject:
            return record.levelno not in self.passlevels
        else:
            return record.levelno in self.passlevels

if __name__ == '__main__':
    LOG_CONF = [{'name': 'operation', 'file': 'log/operation.log',
                 'level': 'DEBUG', 'format': '%(asctime)s %(levelname)s %(message)s'}]
    init_logger(LOG_CONF)
