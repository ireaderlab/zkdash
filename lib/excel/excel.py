#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Copyright (c) 2014,掌阅科技
All rights reserved.

摘    要: 只支持写excel操作，支持多个标签页指定
创 建 者: WangLichao
创建日期: 2014-09-12
'''
import peewee
import xlwt
from StringIO import StringIO
from collections import defaultdict
import datetime
from peewee import Model


class ExcelWorkBook(object):

    '''处理生成excel规则,提供默认样式，导出支持多标签
    '''

    def __init__(self, encoding="utf8"):
        self.excel = xlwt.Workbook(encoding=encoding)
        self.sheets = dict()
        self.sheets_conf = defaultdict(dict)
        self.col_width = 3333  # 3333 = one inch
        self.title_style = self._default_title_style()
        self.text_style = self._default_text_style()

    def add_sheet(self, sheet_name, cell_overwrite_ok=True):
        '''添加表单
        Args:
            sheet_name: 表单名称
        '''
        self.sheets[sheet_name] = self.excel.add_sheet(sheet_name, cell_overwrite_ok)

    def get_sheet(self, sheet_name):
        '''根据表单名获取表单
        '''
        if sheet_name not in self.sheets:
            return None
        return self.sheets[sheet_name]

    def add_title(self, sheet_name, sheet_title, style=None):
        '''给表单添加标题并设置标题样式
        Args:
            sheet_name: 表单名称
            sheet_title: 表单内容的标题,
            举例：({'name': '姓名', 'width': 1},
                   {'name': '年龄', 'width': 1},
                   {'name': '性别', 'width': 2})
            其中name:为标题名称,width占据行宽度
        '''
        sheet = self.get_sheet(sheet_name)
        if not style:
            style = self.title_style
        for row, conf in enumerate(sheet_title):
            sheet.col(row).width = self.col_width * conf.get('width', 1)
            sheet.write(0, row, conf.get('name'), style)
        self.sheets_conf[sheet_name]['title'] = sheet_title

    def add_text(self, sheet_name, sheet_text, bind, style=None, callback=None):
        '''选择sheet并添加内容,单个表单大小不能超过65535行数据
        Args:
            sheet_name: 表单的名称
            sheet_data: 表单的内容,list类型
            bind: 是否绑定变量属性,元祖类型
        '''
        if not isinstance(sheet_text, (list, peewee.SelectQuery)):
            return False
        sheet = self.get_sheet(sheet_name)
        if not style:
            style = self.text_style
        sheet_title = self.sheets_conf[sheet_name].get('title', None)
        if sheet_title and len(sheet_title) != len(bind):
            return False
        for row, row_data in enumerate(sheet_text):
            # 行数进行验证
            if row and row % 65535 == 0:
                new_sheet_name = '{}_{}'.format(sheet_name, row / 65535)
                self.add_sheet(new_sheet_name)
                sheet = self.get_sheet(new_sheet_name)
                # 新的表单页添加标题
                if sheet_title:
                    self.add_title(new_sheet_name, sheet_title)
            # 按列添加到表格中
            for col, key in enumerate(bind):
                val = None
                if callback:
                    val = callback(row_data, key)
                else:
                    if isinstance(row_data, dict):
                        val = row_data.get(key, '')
                    elif isinstance(row_data, Model):
                        val = getattr(row_data, key) or ''
                if isinstance(val, datetime.datetime):
                    val = val.strftime('%Y-%m-%d')
                sheet.write(row % 65535 + 1, col, val, style)
        return True

    def get_stream(self):
        '''获取excle的文件流数据
        Returns:
            返回文件流数据
        '''
        stream = StringIO()
        self.excel.save(stream)
        return stream.getvalue()

    def save(self, file_name):
        '''保存excel到指定文件中
        Args:
            file_name: 指定的excel文件
        '''
        self.excel.save(file_name)

    @staticmethod
    def _default_text_style():
        '''提供默认的文本样式
        '''
        style = xlwt.XFStyle()
        # 左对齐,自动换行
        alignment = xlwt.Alignment()
        alignment.horz = xlwt.Alignment.HORZ_LEFT
        alignment.vert = xlwt.Alignment.VERT_CENTER
        alignment.wrap = xlwt.Alignment.WRAP_AT_RIGHT
        style.alignment = alignment
        return style

    @staticmethod
    def _default_title_style():
        '''提供默认title样式
        '''
        style = xlwt.XFStyle()
        # 字体设置
        font = xlwt.Font()
        font.bold = True  # 宽字体
        font.height = 230
        style.font = font
        # 列设置
        alignment = xlwt.Alignment()
        alignment.horz = xlwt.Alignment.HORZ_LEFT  # 左对齐
        alignment.vert = xlwt.Alignment.VERT_CENTER  # 垂直对齐
        alignment.wrap = xlwt.Alignment.WRAP_AT_RIGHT  # 自动换行
        style.alignment = alignment
        return style
