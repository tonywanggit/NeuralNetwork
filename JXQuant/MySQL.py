import pymysql
from DBUtils.PooledDB import PooledDB

mysqlInfo = {
    "host": '172.16.100.173',
    "user": 'root',
    "passwd": '111111',
    "db": 'neuralnetwork',
    "port": 3306,
    "charset": 'utf8'
}


class MySQL(object):
    __pool = None

    def __init__(self):
        self.conn = MySQL.get_conn()
        self.cursor = self.conn.cursor(cursor=pymysql.cursors.DictCursor)

    @staticmethod
    def get_conn():
        if MySQL.__pool is None:
            __pool = PooledDB(creator=pymysql, mincached=1, maxcached=20, host=mysqlInfo['host'],
                              user=mysqlInfo['user'], passwd=mysqlInfo['passwd'], db=mysqlInfo['db'],
                              port=mysqlInfo['port'], charset=mysqlInfo['charset'])
            print(__pool)
        return __pool.connection()

    def insert(self, sql, params={}):
        try:
            print('insert_sql:', sql, params)
            row_nums = self.cursor.execute(sql, params)
            print('insert_effect_num:', row_nums)
            self.conn.commit()
            return row_nums
        except Exception as e:
            print('insert_fail', e)
            self.conn.rollback()
            self.conn.close()
            return 0

    def update(self, sql, params={}):
        try:
            print('update_sql:', sql, params)
            row_nums = self.cursor.execute(sql, params)
            print('update_effect_num:', row_nums)
            self.conn.commit()
            return row_nums
        except Exception as e:
            print('update_fail', e)
            self.conn.rollback()
            self.conn.close()
            return 0

    def select_one(self, sql, params={}):
        try:
            self.cursor.execute(sql, params)
            select_res = self.cursor.fetchone()
            return select_res
        except Exception as e:
            print('select_fail', e)
            return None

    def select_all(self, sql, params={}):
        try:
            self.cursor.execute(sql, params)
            select_res = self.cursor.fetchall()
            return select_res
        except Exception as e:
            print('select_fail', e)
            return None

    def dispose(self):
        self.conn.close()
        self.cursor.close()
        
        
if __name__ == '__main__':
        mysql = MySQL()

        sql = "select * from my_capital"
        res = mysql.select_one(sql)

        mysql.dispose()
        print(res)
