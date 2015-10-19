#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014,掌阅科技
All rights reserved.

摘    要: database.py
创 建 者: WangLichao
创建日期: 2015-01-26
"""
# pylint: disable=invalid-name, bare-except
from lib.db.retrydb import MyRetryDB
from peewee import Model as _Model
from peewee import DoesNotExist
from peewee import OperationalError


class Database(object):

    '''db封装,自动查找数据库
    '''

    def __init__(self, **connect_kwargs):
        self.connect_kwargs = connect_kwargs
        self.load_database()
        self.Model = self.get_model_class()

    def load_database(self):
        self.db = self.connect_kwargs.pop('db')
        self.database = MyRetryDB(self.db, **self.connect_kwargs)
        self.database.field_overrides.update({'enum': 'enum'})  # 增加枚举类型

    def get_model_class(self):
        '''获取基类model
        '''
        class BaseModel(_Model):

            '''BaseModel的封装
            '''

            class Meta(object):
                '''元类
                '''
                database = self.database

            @classmethod
            def one(cls, *query, **kwargs):
                '''获取单条数据
                Retruns:
                    返回单条数据不存在则返回None
                '''
                try:
                    return cls.get(*query, **kwargs)
                except DoesNotExist:
                    return None

            def delete_instance(self, *args, **kwargs):
                '''如果deleted字段存在自动使用逻辑删除
                '''
                if 'deleted' in self._meta.fields:
                    setattr(self, 'deleted', '1')
                    super(BaseModel, self).save()
                else:
                    super(BaseModel, self).delete_instance(*args, **kwargs)

            def __hash__(self):
                """提供hash支持
                """
                return hash(self.id)

        return BaseModel

    def connect(self):
        '''主从建立连接,如果连接关闭重试
        '''
        i = 0
        while i < 4:
            try:
                if self.database.is_closed():
                    self.database.get_conn().ping(True)
                break
            except OperationalError:
                self.close()
                i = i + 1

    def close(self):
        '''关闭连接
        '''
        try:
            self.database.close()
        except:
            pass
