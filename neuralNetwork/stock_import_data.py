import tushare as ts
from sqlalchemy import create_engine

if __name__ == '__main__':
    ts.set_token('E83fb68e2e009d139c1522bc6191100e9ab2a5933f19c25e49d04151')
    pro = ts.pro_api()
    df = pro.trade_cal(exchange='', start_date='20150901', end_date='20190421', fields='exchange,cal_date,is_open,pretrade_date', is_open='0')
    stock_basic = pro.stock_basic(list_status='L')

    db = create_engine('mysql+pymysql://root:111111@172.16.100.173:3306/neuralnetwork?charset=utf8')
    stock_basic.to_sql('stock_basic', db, index=False, if_exists='append')

    # db = create_engine('mysql+pymysql://root:111111@172.16.100.173:3306/neuralnetwork?charset=utf8')
    # daily = pro.daily(ts_code='002230.SZ', start_date='20150101', fields='ts_code,trade_date,open,close,pre_close,high,low,vol,amount')
    # daily.to_sql('stock_daily', db, index=False, if_exists='append')


    print(stock_basic)