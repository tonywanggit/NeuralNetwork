import pymysql


def cap_update_daily(state_dt):
    """添加一条当天的投资账户记录"""

    para_norisk = (1.0 + 0.04 / 365)
    db = pymysql.connect(host='172.16.100.173', port=3306, user='root', passwd='111111', db='neuralnetwork',
                         charset='utf8')
    cursor = db.cursor()
    sql_pool = "select * from my_stock_pool"
    cursor.execute(sql_pool)
    done_set = cursor.fetchall()
    db.commit()
    new_lock_cap = 0.00
    for i in range(len(done_set)):
        stock_code = str(done_set[i][0])
        stock_vol = float(done_set[i][2])
        sql = "select close from stock_daily a where a.ts_code = '%s' and a.trade_date <= '%s' " \
              "order by a.trade_date desc limit 1" % (stock_code, state_dt)
        cursor.execute(sql)
        done_temp = cursor.fetchall()
        db.commit()
        if len(done_temp) > 0:
            cur_close_price = float(done_temp[0][0])
            new_lock_cap += cur_close_price * stock_vol
        else:
            print('Cap_Update_daily Err!!')
            raise Exception
    sql_cap = "select money_rest from my_capital order by seq asc"
    cursor.execute(sql_cap)
    done_cap = cursor.fetchall()
    db.commit()
    new_cash_cap = float(done_cap[-1][0]) * para_norisk
    new_total_cap = new_cash_cap + new_lock_cap
    sql_insert = "insert into my_capital(capital,money_lock,money_rest,bz,state_dt)" \
                 "values('%.2f','%.2f','%.2f','%s','%s')" % (
                     new_total_cap, new_lock_cap, new_cash_cap, str('Daily_Update'), state_dt)
    cursor.execute(sql_insert)
    db.commit()
    return 1
