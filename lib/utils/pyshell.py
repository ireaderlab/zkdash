#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Copyright (c) 2013,掌阅科技
All rights reserved.

File Name: pyshell.py
Author: WangLichao
Created on: 2014-03-21
'''
import subprocess
import time


def wait_process_end(process, timeout):
    '''等待进程终止
    Args:
        process: 进程句柄
        timeout: 超时时间
    Returns:
        与shell的执行保持一致
        0:成功
        1:超时
        2:错误
    '''
    if timeout <= 0:
        process.wait()
        return 0
    start_time = time.time()
    end_time = start_time + timeout
    while 1:
        ret = process.poll()
        if ret == 0:
            return 0
        elif ret is None:
            cur_time = time.time()
            if cur_time >= end_time:
                return 1
            time.sleep(0.1)
        else:
            return 2


class ShellResult(object):

    '''封装shell执行的返回结果形式
    Attributes:
        return_code: 返回码
        stdout：标准输出
        stderr: 错误输出
    '''

    def __init__(self, return_code, stdout, stderr):
        self.return_code = return_code
        self.stdout = stdout
        self.stderr = stderr


def shell(command, timeout=0, capture=False, debug=False):
    '''用于执行本地shell的功能
    Args:
        command: bash命令
        timeout: 命令的超时时间
        capture: 是否捕获输出结果
        debug: 是否输出debug信息
    Returns:
        返回ShellResult对象
    '''
    if debug:
        print '=' * 35
        print '[local] ' + command
        print '=' * 35
    if capture:
        process = subprocess.Popen(command, stdin=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   shell=True)
    else:
        process = subprocess.Popen(command, shell=True)
    ret = wait_process_end(process, timeout)
    if ret == 1:
        process.terminate()
        raise Exception("terminated_for_timout")
    if capture:
        stdout = ''.join(process.stdout.readlines())
        stderr = ''.join(process.stderr.readlines())
        return ShellResult(process.returncode, stdout, stderr)
    else:
        return ShellResult(process.returncode, None, None)
