import logging

import pymysql
import mysql_config as Config
from DBUtils.PooledDB import PooledDB


class MySql(object):
    mysql = None

    def __init__(self):
        self.db = PTConnectionPool()

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'inst'):
            cls.inst = super(MySql, cls).__new__(cls, *args, **kwargs)
        return cls.inst

    @classmethod
    def instance(cls):
        if MySql.mysql is None:
            MySql.mysql = MySql()

        return MySql.mysql

    def select(self, sql, param={}):
        try:
            cursor, conn = self.execute(sql, param)
            res = cursor.fetchall()
            self.close(cursor, conn)
            return res
        except Exception as e:
            logging.exception('selectall except   ', e)
            self.close(cursor, conn)
            return None

    def select_one(self, sql, param={}):
        try:
            cursor, conn = self.execute(sql, param)
            res = cursor.fetchone()
            self.close(cursor, conn)
            return res
        except Exception as e:
            logging.exception('selectone except   ', e)
            self.close(cursor, conn)
            return None

    def insert(self, sql, param={}):
        try:
            cursor, conn = self.execute(sql, param)
            _id = cursor.lastrowid
            conn.commit()
            self.close(cursor, conn)
            # 防止表中没有id返回0
            if _id == 0:
                return True
            return _id
        except Exception as e:
            print('insert except   ', e.args)
            conn.rollback()
            self.close(cursor, conn)
            return 0

    def insert_many(self, sql, param={}):
        cursor, conn = self.db.get_conn()
        try:
            cursor.executemany(sql, param)
            conn.commit()
            self.close(cursor, conn)
            return True
        except Exception as e:
            print('insert many except   ', e.args)
            conn.rollback()
            self.close(cursor, conn)
            return False

    def delete(self, sql, param={}):
        try:
            cursor, conn = self.execute(sql, param)
            self.close(cursor, conn)
            return True
        except Exception as e:
            print('delete except   ', e.args)
            conn.rollback()
            return False

    # 更新
    def update(self, sql, param={}):
        try:
            cursor, conn = self.execute(sql, param)
            self.close(cursor, conn)
            return True
        except Exception as e:
            print('update except   ', e.args)
            conn.rollback()
            self.close(cursor, conn)
            return False

    # 执行命令
    def execute(self, sql, param={}, autoclose=False):
        cursor, conn = self.db.get_conn()
        try:
            if param:
                cursor.execute(sql, param)
            else:
                cursor.execute(sql)
            conn.commit()
            if autoclose:
                self.close(cursor, conn)
        except Exception as e:
            print('execute except   ', e)
            logging.exception(e)
            pass
        return cursor, conn

    # 执行多条命令
    '[{"sql":"xxx","param":"xx"}....]'

    def executemany(self, list=[]):
        cursor, conn = self.db.get_conn()
        try:
            for order in list:
                sql = order['sql']
                param = order['param']
                if param:
                    cursor.execute(sql, param)
                else:
                    cursor.execute(sql)
            conn.commit()
            self.close(cursor, conn)
            return True
        except Exception as e:
            print('execute failed========', e.args)
            conn.rollback()
            self.close(cursor, conn)
            return False

    def close(self, cursor, conn):
        cursor.close()
        conn.close()


def new_db():
    """创建一个数据库实例"""
    return MySql.instance()


class PTConnectionPool(object):
    """MySQL链接池"""
    __pool = None

    def __enter__(self):
        self.conn = self.__get_conn()
        self.cursor = self.conn.cursor()
        print("PT数据库创建con和cursor")
        return self

    def __get_conn(self):
        if self.__pool is None:
            self.__pool = PooledDB(creator=pymysql, mincached=Config.DB_MIN_CACHED, maxcached=Config.DB_MAX_CACHED,
                                   maxshared=Config.DB_MAX_SHARED, maxconnections=Config.DB_MAX_CONNECTIONS,
                                   blocking=Config.DB_BLOCKING, maxusage=Config.DB_MAX_USAGE,
                                   setsession=Config.DB_SET_SESSION,
                                   host=Config.DB_TEST_HOST, port=Config.DB_TEST_PORT,
                                   user=Config.DB_TEST_USER, passwd=Config.DB_TEST_PASSWORD,
                                   db=Config.DB_TEST_DBNAME, use_unicode=True, charset=Config.DB_CHARSET)
        return self.__pool.connection()

    def __exit__(self, type, value, trace):
        """
            @summary: 释放连接池资源
        """
        self.cursor.close()
        self.conn.close()
        print("PT连接池释放con和cursor")

    def get_conn(self):
        conn = self.__get_conn()
        cursor = conn.cursor()
        return cursor, conn


if __name__ == '__main__':
    mysql = MySql.instance()
    # result = mysql.select_one("select * from my_capital where seq = %s and bz=%s", [1, "INIT"])
    # print(result)

    result = mysql.select_one("select * from stock_basic where ts_code = %s", '000001.SZ')
    print(result)

    # sql_insert = "insert into my_capital(capital,money_lock,money_rest,bz,state_dt)" \
    #              "values(%s, %s, %s, %s, %s)"
    # mysql.insert(sql_insert, [round(10.11, 2), round(20.33633, 2), 0.0, str('Daily_Update'), '60'])
