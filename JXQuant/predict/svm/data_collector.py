# -*- coding:utf8 -*-
import numpy as np
from datasource import mysql


class DataCollector(object):
    """数据预处理"""

    def __init__(self, ts_code, start_dt, end_dt):
        self.make_data_collect(ts_code, start_dt, end_dt)

    def make_data_collect(self, ts_code, start_dt, end_dt):
        """制作训练用的数据集"""

        # 建立数据库连接，获取日线基础行情(开盘价，收盘价，最高价，最低价，成交量，成交额)
        db = mysql.new_db()
        sql_done_set = "SELECT trade_date, ts_code, open, close, high, low, vol, amount FROM stock_daily " \
                       "where ts_code = %s and trade_date >= %s and trade_date <= %s order by trade_date asc"
        done_set = db.select(sql_done_set, (ts_code, start_dt, end_dt))

        if len(done_set) == 0:
            raise Exception

        self.date_seq = []
        self.open_list = []
        self.close_list = []
        self.high_list = []
        self.low_list = []
        self.vol_list = []
        self.amount_list = []
        for i in range(len(done_set)):
            self.date_seq.append(done_set[i][0])
            self.open_list.append(float(done_set[i][2]))
            self.close_list.append(float(done_set[i][3]))
            self.high_list.append(float(done_set[i][4]))
            self.low_list.append(float(done_set[i][5]))
            self.vol_list.append(float(done_set[i][6]))
            self.amount_list.append(float(done_set[i][7]))

        # 将日线行情整合为训练集(其中self.train是输入集，self.target是输出集，self.test_case是end_dt那天的单条测试输入)
        self.data_train = []
        self.data_target = []
        self.data_target_onehot = []
        self.cnt_pos = 0
        self.test_case = []

        for i in range(1, len(self.close_list)):
            train = [self.open_list[i - 1], self.close_list[i - 1], self.high_list[i - 1], self.low_list[i - 1],
                     self.vol_list[i - 1], self.amount_list[i - 1]]
            self.data_train.append(np.array(train))

            if self.close_list[i] / self.close_list[i - 1] > 1.0:
                self.data_target.append(float(1.00))
                self.data_target_onehot.append([1, 0, 0])
            else:
                self.data_target.append(float(0.00))
                self.data_target_onehot.append([0, 1, 0])
        self.cnt_pos = len([x for x in self.data_target if x == 1.00])
        self.test_case = np.array(
            [self.open_list[-1], self.close_list[-1], self.high_list[-1], self.low_list[-1], self.vol_list[-1],
             self.amount_list[-1]])
        self.data_train = np.array(self.data_train)
        self.data_target = np.array(self.data_target)
        return 1
