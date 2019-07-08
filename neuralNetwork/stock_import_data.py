import time

import tushare as ts
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from datetime import timedelta

from neuralNetwork.data_model import StockInfo

db = create_engine('mysql+pymysql://root:111111@172.16.100.173:3306/neuralnetwork?charset=utf8')
DBSession = sessionmaker(bind=db)
ts.set_token('17642bbd8d39b19c02cdf56002196c8709db65ce14ee62e08935ab0c')
pro = ts.pro_api()


def import_stock(stock_code, start_data):
    daily = pro.daily(ts_code=stock_code, start_date=start_data,
                      fields='ts_code,trade_date,open,close,pre_close,high,low,vol,amount')
    daily.to_sql('stock_daily', db, index=False, if_exists='append')
    if daily.shape[0] > 0:
        update_stock_info(stock_code, daily['trade_date'].max())


def update_stock_info(stock_code, new_trade_date):
    session = DBSession()
    stock_info = StockInfo(ts_code=stock_code, update_date=new_trade_date)
    session.merge(stock_info)
    session.commit()
    session.close()


if __name__ == '__main__':
    # import_stock('000002.SZ', '19910129')

    stock_list = pd.read_sql(sql='select ts_code, list_date from stock_basic where update_date  < %(last_update)s or '
                                 'update_date is null', con=db, params={'last_update': '20190620'})
    stock_update_date = pd.read_sql(
        sql='select ts_code, max(trade_date) as update_date  from stock_daily group by ts_code', con=db)
    for index, row in stock_list.iterrows():
        start_time = time.time()
        stock_daily_max_trade_date = stock_update_date[stock_update_date.ts_code == row['ts_code']]
        start_date = row['list_date']
        if stock_daily_max_trade_date.shape[0] > 0:
            update_date = datetime.strptime(stock_daily_max_trade_date[0:1]['update_date'].values[0], '%Y%m%d').date()
            start_date = (update_date + timedelta(days=1)).strftime('%Y%m%d')

        import_stock(row['ts_code'], start_date)
        time.sleep(0.3)
        print(row['ts_code'], time.time() - start_time)
