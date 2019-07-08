# -*- coding: utf-8 -*-
# @Time    : 2019/6/19 9:00
# @Author  : Tony
"""VEGAS隧道交易算法"""

import numpy as np
import pandas as pd
import talib

from datasource import mysql

db = mysql.new_db()


def is_vegas_stock(ts_code):
    begin_date = "20181001"
    stock_daily_sql = "select trade_date, close from stock_daily " \
                      "where ts_code = %s and trade_date > %s order by trade_date asc"
    stock_daily_rs = db.select(stock_daily_sql, [ts_code, begin_date])
    close_array = np.array([float(x[1]) for x in stock_daily_rs])
    sma_12 = talib.SMA(close_array, 12)
    sma_144 = talib.SMA(close_array, 144)
    sma_169 = talib.SMA(close_array, 169)

    stock_daily_df = pd.DataFrame(list(stock_daily_rs), columns=['trade_date', 'close'])
    stock_daily_df["sma_12"] = sma_12
    stock_daily_df["sma_144"] = sma_144
    stock_daily_df["sma_169"] = sma_169

    window = 4
    uplift = 0.04

    try:
        return vegas_judge(ts_code, stock_daily_df.tail(window), window, uplift)
    except Exception as e:
        print("----exception----{}---{}---------".format(ts_code, e))
        print(stock_daily_df.tail(window))
        return True


def vegas_judge(ts_code, data_last_five, window, min_uplift):
    if data_last_five.shape[0] < window:
        return False
    stock_daily_tail5 = data_last_five.tail(window)
    sma12_start = stock_daily_tail5.iloc[0, 2]
    sma12_end = stock_daily_tail5.iloc[window - 1, 2]
    sma_low_min = min(stock_daily_tail5.iloc[0, 3], stock_daily_tail5.iloc[0, 4])
    sma_up_max = max(stock_daily_tail5.iloc[window - 1, 3], stock_daily_tail5.iloc[window - 1, 4])
    uplift = (sma12_end - sma12_start) / sma12_start
    if sma12_start < sma_low_min and sma12_end > sma_up_max and sma12_start < sma12_end \
            and min_uplift < uplift < 0.8 and not ts_code.startswith("300"):
        print(f"-------------{ts_code}---{uplift}---------")
        # print("-------------{}---{}---------".format(ts_code, uplift))
        print(stock_daily_tail5)
        return True
    else:
        return False


if __name__ == '__main__':
    last_trade_date = "20190620"
    stock_all_sql = "select ts_code from stock_daily group by ts_code having max(trade_date) > %s"
    stock_all_rs = db.select(stock_all_sql, [last_trade_date])

    for i in range(len(stock_all_rs)):
        is_vegas_stock(stock_all_rs[i][0])
