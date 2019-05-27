from datasource import mysql


def cap_update_daily(state_dt):
    """添加一条当天的投资账户记录"""

    para_norisk = (1.0 + 0.04 / 365)
    db = mysql.new_db()

    sql_pool = "select * from my_stock_pool"
    done_set = db.select(sql_pool)
    new_stock_money = 0.00  # 根据当天的收盘价计算持仓股票的价值
    for i in range(len(done_set)):
        stock_code = str(done_set[i][0])
        stock_vol = float(done_set[i][2])
        sql = "select close from stock_daily a where a.ts_code = %s and a.trade_date <= %s " \
              "order by a.trade_date desc limit 1"  # 获取股票在回测日期的收盘价
        stock_close_price = db.select_one(sql, [stock_code, state_dt])

        if len(stock_close_price) > 0:
            cur_close_price = float(stock_close_price[0])
            new_stock_money += cur_close_price * stock_vol
        else:
            print('Cap_Update_daily Err!!')
            raise Exception

    # 查找上一个交易日的可用现金余额，并计算回测交易日的现金、股票金额、总金额
    sql_capital = "select money_rest from my_capital order by seq desc limit 1"
    last_capital_record = db.select_one(sql_capital)

    new_cash = float(last_capital_record[0]) * para_norisk
    new_total = new_cash + new_stock_money
    sql_insert = "insert into my_capital(capital,money_lock,money_rest,bz,state_dt) values(%s, %s, %s, %s, %s)"
    db.insert(sql_insert, [round(new_total, 2), round(new_stock_money, 2), round(new_cash, 2), 'DailyUpdate', state_dt])
    return 1
