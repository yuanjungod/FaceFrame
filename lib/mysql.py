# -*- coding:utf-8 -*-

import pymysql
import pymysql.cursors
import logging
import pandas as pd

__all__ = ['MysqlClient']


class MysqlClient(object):

    logger = logging.getLogger('logger')

    def __init__(self, host='', user='', password='', port=3306, charset='utf8'):
        print("mysql client init")
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.charset = charset
        self.link = None
        self.cursor = None

    def connect(self):
        try:
            self.link = pymysql.connect(host=self.host, user=self.user, passwd=self.password, port=int(self.port),
                                        charset=self.charset,
                                        cursorclass=pymysql.cursors.DictCursor)
            self.cursor = self.link.cursor()
        except pymysql.Error as e:
            self.logger.error('Error code: %s, message: %s, host: %s, user: %s, port: %s' %
                              (e.args[0], e.args[1], self.host, self.user, self.port))

    def select(self, field='*', table_name='', where=''):

        if where:
            sql = "SELECT %s FROM %s WHERE %s" % (field, table_name, where)
        else:
            sql = "SELECT %s FROM %s" % (field, table_name)

        self.execute(sql)
        self.commit()
        return self.all()

    def pandas_select(self, field='*', table_name='', where=''):

        if self.link is None:
            self.connect()

        if where:
            sql = "SELECT %s FROM %s WHERE %s" % (field, table_name, where)
        else:
            sql = "SELECT %s FROM %s" % (field, table_name)

        return pd.read_sql(sql, self.link)

    def join(self, field='*', last_table_name='', first_table_name='', join_with='', where=''):

        if where:
            sql = "SELECT %s FROM %s JOIN %s ON %s WHERE %s" % (
                field, last_table_name, first_table_name, join_with, where)
        else:
            sql = "SELECT %s FROM %s JOIN %s ON %s" % (field, last_table_name, first_table_name, join_with)

        self.execute(sql)
        self.commit()
        return self.all()

    def update(self, table_name, params, where=''):

        if not isinstance(params, dict):
            self.logger.error(message="update() params:%s" % params)
            return 0

        update_field = ",".join(map(lambda param: str(param[0]) + " = " + str('null')
                if param[1] is None else
                str(param[0]) + " = '" + pymysql.escape_string(str(param[1])) + "'", params.items()))

        if where:
            sql = "UPDATE %s SET %s WHERE %s" % (table_name, update_field, where)
        else:
            sql = "UPDATE %s SET %s" % (table_name, update_field)

        res = 1
        try:
            self.execute(sql)
            self.commit()
        except pymysql.Error as e:
            self.logger.error('Error code: %s, message: %s, sql: %s' % (e.args[0], e.args[1], sql))
            res = 0
        return res

    def insert(self, table_name, params):

        if not isinstance(params, dict):
            self.logger.error("insert() params:%s" % params)
            return 0

        insert_filed = ",".join(map(lambda param: str(param[0]), params.items()))

        insert_value = ",".join(map(lambda param: 'null' if param[1] is None else
                        "'" + pymysql.escape_string(str(param[1])) + "'", params.items()))

        sql = 'insert into %s (%s) values(%s);' % (table_name, insert_filed, insert_value)

        res = 1
        try:
            self.execute(sql)
            self.commit()
        except pymysql.Error as e:
            self.logger.error('Error code: %s, message: %s, sql: %s' % (e.args[0], e.args[1], sql))
            res = 0

        return res

    def batch_insert(self, table_name, params_list):

        if not params_list or not isinstance(params_list, list) or len(params_list) == 0 or \
                not isinstance(params_list[0], dict):
            self.logger.error("batch_insert() params:%s", params_list)
            return 0

        succeed_num = 0
        params_list = sorted(params_list, key=lambda params: params.keys())
        insert_list = [params_list[0]]

        for i in range(1, len(params_list)):
            if cmp(params_list[i - 1].keys(), params_list[i].keys()) != 0:
                sql = "insert into %s (%s) values(%s)" % (table_name, ','.join(insert_list[0].keys()),
                                                           ','.join(['%s' for j in range(len(insert_list[0]))]))
                insert_values = map(lambda insert_value: insert_value.values(), insert_list)

                try:
                    current_num = self.executemany(sql, insert_values)
                    succeed_num += current_num
                    self.commit()
                except pymysql.Error as e:
                    self.logger.error('Error code: %s, message: %s' % (e.args[0], e.args[1]))

                insert_list = []

            insert_list.append(params_list[i])

        sql = "insert into %s (%s) values(%s)" % (table_name, ','.join(insert_list[0].keys()),
                                                   ','.join(['%s' for j in range(len(insert_list[0]))]))

        insert_values = map(lambda insert_value: insert_value.values(), insert_list)

        try:
            current_num = self.executemany(sql, insert_values)
            succeed_num += current_num
            self.commit()
        except pymysql.Error as e:
            self.logger.error('Error code: %s, message: %s, sql: %s' % (e.args[0], e.args[1], sql))

        return succeed_num

    def replace(self, table_name, params):

        if not params or not isinstance(params, dict):
            self.logger.debug(params)
            return 0

        replace_filed = ",".join(map(lambda param: param[0], params.items()))
        replace_value = ",".join(map(
            lambda param: 'null' if param[1] is None else
            "'" + pymysql.escape_string(str(param[1])) + "'", params.items()))

        sql = 'replace into %s (%s) values(%s);' % (table_name, replace_filed, replace_value)

        res = 1
        try:
            self.execute(sql)
            self.commit()
        except pymysql.Error as e:
            self.logger.error('Error code: %s, message: %s, sql: %s' % (e.args[0], e.args[1], sql))
            res = 0

        return res

    def batch_replace(self, table_name, params_list):

        if not params_list or not isinstance(params_list, list) or len(params_list) == 0 or \
                not isinstance(params_list[0], dict):
            self.logger.error("batch_replace() params:%s", params_list)
            return 0

        succeed_num = 0
        params_list = sorted(params_list, key=lambda params: params.keys())
        insert_list = [params_list[0]]
        for i in range(1, len(params_list)):
            if cmp(params_list[i - 1].keys(), params_list[i].keys()) != 0:
                sql = "replace into %s (%s) values(%s)" % (
                    table_name, ','.join(insert_list[0].keys()),
                    ','.join(['%s' for j in range(len(insert_list[0]))]))
                insert_values = map(lambda insert_value: insert_value.values(), insert_list)

                try:
                    res = self.executemany(sql, insert_values)
                    if res > 0:
                        succeed_num += len(insert_list)
                    self.commit()
                except pymysql.Error as e:
                    self.logger.error('Error code: %s, message: %s' % (e.args[0], e.args[1]))
                insert_list = []

            insert_list.append(params_list[i])

        sql = "replace into %s (%s) values(%s)" % (table_name, ','.join(insert_list[0].keys()),
                                                  ','.join(['%s' for j in range(len(insert_list[0]))]))
        insert_values = map(lambda insert_value: insert_value.values(), insert_list)
        try:
            res = self.executemany(sql, insert_values)
            if res > 0:
                succeed_num += len(insert_list)
            self.commit()
        except pymysql.Error as e:
            self.logger.error('Error code: %s, message: %s, sql: %s' % (e.args[0], e.args[1], sql))

        return succeed_num

    def delete(self, table_name='', where=''):
        res = True
        if where:
            sql = "DELETE FROM %s WHERE %s" % (table_name, where)
        else:
            sql = "DELETE FROM %s" % (table_name)
        try:
            self.execute(sql)
            self.commit()
        except pymysql.Error as e:
            self.logger.error('Error code: %s, message: %s, sql: %s' % (e.args[0], e.args[1], sql))
            res = False

        return res

    def insert_id(self):
        return self.link.insert_id()

    def execute(self, sql):

        res = False
        try_count = 3
        if self.cursor is None:
            self.connect()

        while try_count > 0 and res is False:

            res = True
            try:
                self.cursor.execute(sql)
            except pymysql.Error as e:
                self.logger.error('Error code: %s, message: %s, sql: %s' % (e.args[0], e.args[1], sql))
                self.connect()
                res = False
            try_count -= 1

        return res

    def executemany(self, sql, values):
        try_count = 3
        res = 0
        if self.cursor is None:
            self.connect()
        while try_count > 0 and res is 0:
            try:
                res = self.cursor.executemany(sql, values)
            except pymysql.Error as e:
                self.logger.error('Error code: %s, message: %s' % (e.args[0], e.args[1]))
                self.connect()
            try_count -= 1
        return res

    def all(self):
        res = []
        if self.cursor is not None:
            res = self.cursor.fetchall()

        return res

    def one(self):
        res = None
        if self.cursor is not None:
            res = self.cursor.fetchone()

        return res

    def commit(self):
        self.link.commit()

    def close(self):
        self.cursor.close()
        self.link.close()