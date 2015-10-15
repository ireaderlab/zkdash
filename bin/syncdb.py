#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Copyright (c) 2014,掌阅科技
All rights reserved.

摘    要: syncdb.py
创 建 者: zhuangshixiong
创建日期: 2015-10-10
'''
# pylint: disable=import-error, unused-variable, protected-access
import sys
import os
import pkgutil
sys.path.append(os.path.dirname(os.path.split(os.path.realpath(__file__))[0]))

import model.db
from model.db.base import ZKDASH_DB
from lib.utils import find_subclasses


def sync_db():
    """sync db
    """
    # firstly, import all modules of model.db package
    prefix = model.db.__name__ + "."
    for importer, modname, ispkg in pkgutil.iter_modules(model.db.__path__, prefix):
        __import__(modname)

    # then, find all subclasses of WARSHIP_DB.Model
    models = find_subclasses(ZKDASH_DB.Model)
    for mod in models:
        if mod.table_exists():
            print "table exists: %s, drop it!" % mod._meta.db_table
            mod.drop_table()
        mod.create_table()
        print "created table: %s" % mod._meta.db_table


if __name__ == '__main__':
    sync_db()
