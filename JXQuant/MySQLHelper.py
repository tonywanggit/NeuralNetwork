from MySqlConnection import getPTConnection
import logging


class MySqlHelper(object):
    mysql = None

    def __init__(self):
        self.db = getPTConnection()

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'inst'):
            cls.inst = super(MySqlHelper, cls).__new__(cls, *args, **kwargs)
        return cls.inst

    @classmethod
    def instance(cls):
        if MySqlHelper.mysql is None:
            MySqlHelper.mysql = MySqlHelper()

        return MySqlHelper.mysql

    def select_all(self, sql, param={}):
        try:
            cursor, conn = self.execute(sql, param)
            res = cursor.fetchall()
            self.close(cursor, conn)
            return res
        except Exception as e:
            print('selectall except   ', e.args)
            self.close(cursor, conn)
            return None

    def select_one(self, sql, param={}):
        try:
            cursor, conn = self.execute(sql, param)
            res = cursor.fetchone()
            self.close(cursor, conn)
            return res
        except Exception as e:
            print('selectone except   ', e.args)
            self.close(cursor, conn)
            return None

    def insert(self, sql, param={}):
        try:
            cursor, conn = self.execute(sql, param)
            _id = cursor.lastrowid
            print('_id   ', _id)
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


if __name__ == '__main__':
    mysql = MySqlHelper.instance()
    result = mysql.select_all("select * from my_capital where seq = %s", [149])
    print(result)
