#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

"""
Copyright (c) 2014,掌阅科技
All rights reserved.

摘    要: zd_qconf_feedback.py
创 建 者: zhuangshixiong
创建日期: 2015-06-24
"""

from peewee import DateTimeField
from peewee import CharField
from peewee import IntegerField
from peewee import SQL

from model.db.base import ZKDASH_DB, EnumField


class ZdQconfFeedback(ZKDASH_DB.Model):

    """ZdQconfFeedback Model
    """

    id = IntegerField(primary_key=True, constraints=[SQL("AUTO_INCREMENT")])
    hostname = CharField(max_length=32, null=True)
    ip = CharField(max_length=32, null=True)
    path = CharField(max_length=512, null=True)
    md5_value = CharField(max_length=128, null=True)
    idc = CharField(max_length=32, null=True)
    update_time = DateTimeField(null=True)
    data_type = CharField(null=True)
    execute_status = EnumField(enum_value="'0', '1', '2'", constraints=[SQL("DEFAULT '0'")])
    deleted = EnumField(enum_value="'0', '1'", constraints=[SQL("DEFAULT '0'")])

    class Meta(object):

        """表配置信息
        """
        db_table = "zd_qconf_feedback"
