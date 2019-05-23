import datetime as dt
import tushare as ts

ts.set_token('17642bbd8d39b19c02cdf56002196c8709db65ce14ee62e08935ab0c')
pro = ts.pro_api()


def get_trade_date_seq(start_date, end_date):
    """获取某个时间段的交易日期序列"""

    df = pro.trade_cal(exchange_id='', is_open=1, start_date=start_date, end_date=end_date)
    date_seq = list(df.iloc[:, 1])
    return date_seq


def build_test_date_seq(state_dt, para_window):
    """构建回测时间序列

    state_dt    交易序列结束时间
    
    para_window 回测窗口长度
    """
    start_date = (dt.datetime.strptime(state_dt, '%Y%m%d') - dt.timedelta(days=para_window)).strftime('%Y%m%d')
    df = pro.trade_cal(exchange_id='', is_open=1, start_date=start_date, end_date=state_dt)
    return list(df.iloc[:, 1])
