# -*- coding: utf-8 -*-
# @Time    : 2019/6/26 8:42
# @Author  : Tony
"""双均线策略"""

import pandas as pd
import matplotlib.pyplot as plt

from datasource import mysql

db = mysql.new_db()

data = pd.read_sql("select trade_date, close from stock_daily "
                         "where ts_code = '000686.SZ' and trade_date > '20190501' order by trade_date asc",
                   db.get_conn())

data['change'] = data['close'] - data['close'].shift(1)
data['ma5'] = data['close'].rolling(window=5, center=False).mean()
data['ma20'] = data['close'].rolling(window=20, center=False).mean()

data = data.dropna()

data['pos'] = 0
data['pos'][data['ma5'] >= data['ma20']] = 10000
data['pos'][data['ma5'] < data['ma20']] = -10000
data['pos'] = data['pos'].shift(1).fillna(0)

data['pnl'] = data['pos'] * data['change']
data['fee'] = 0
data['fee'][data['pos'] != data['pos'].shift(1)] = 20000 * data['close'] * 3 / 10000
data['netpnl'] = data['pnl'] - data['fee']
data['cumpnl'] = data['netpnl'].cumsum()

print(data)

data['cumpnl'].plot()
plt.show()