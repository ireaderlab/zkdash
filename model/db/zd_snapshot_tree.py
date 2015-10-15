#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

"""
Copyright (c) 2014,掌阅科技
All rights reserved.

摘    要: zd_snapshot_tree.py
创 建 者: zhuangshixiong
创建日期: 2015-09-02
"""

from peewee import CharField
from peewee import IntegerField
from peewee import SQL

from model.db.base import ZKDASH_DB


class ZdSnapshotTree(ZKDASH_DB.Model):

    """ZdSnapshotTree Model
    """

    id = IntegerField(primary_key=True, constraints=[SQL("AUTO_INCREMENT")])
    cluster_name = CharField(max_length=64, null=True)
    node_path = CharField(max_length=512, null=True)
    left = IntegerField(null=True)
    right = IntegerField(null=True)

    class Meta(object):

        """表配置信息
        """
        db_table = "zd_snapshot_tree"
