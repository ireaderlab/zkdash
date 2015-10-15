#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

"""
Copyright (c) 2014,掌阅科技
All rights reserved.

摘    要: zd_zookeeper.py
创 建 者: zhuangshixiong
创建日期: 2015-06-23
"""

from peewee import CharField
from peewee import IntegerField
from peewee import SQL

from model.db.base import ZKDASH_DB, EnumField


class ZdZookeeper(ZKDASH_DB.Model):

    """ZdZookeeper Model
    """

    id = IntegerField(primary_key=True, constraints=[SQL("AUTO_INCREMENT")])
    cluster_name = CharField(max_length=32)
    hosts = CharField(max_length=128)
    business = CharField(max_length=255)
    deleted = EnumField(enum_value="'0', '1'", constraints=[SQL("DEFAULT '0'")])

    class Meta(object):

        """表配置信息
        """
        db_table = "zd_zookeeper"
