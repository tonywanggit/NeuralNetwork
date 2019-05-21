import account
import mysql
import trade_operator


def operate_stock(stock_new, state_dt, predict_dt, poz):
    db = mysql.new_db()

    # 先更新持股天数
    sql_update_hold_days = 'update my_stock_pool w set w.hold_days = w.hold_days + 1'
    db.update(sql_update_hold_days)

    # 先卖出
    deal_account = account.CurrentAccount(state_dt)
    stock_pool_local = deal_account.stock_pool
    for stock in stock_pool_local:
        sql_predict = "select predict from model_ev_resu where state_dt = %s and stock_code = %s"
        predict_stock_record = db.select_one(sql_predict, (predict_dt, stock))

        predict = 0
        if predict_stock_record is not None:
            predict = int(predict_stock_record[0])
        trade_operator.sell(stock, state_dt, predict)

    # 后买入
    for stock_index in range(len(stock_new)):
        deal_buy = account.CurrentAccount(state_dt)

        # # 如果模型f1分值低于50则不买入
        # sql_f1_check = "select * from model_ev_resu a where a.stock_code = '%s' and a.state_dt < '%s' order by a.state_dt desc limit 1"%(stock_new[stock_index],state_dt)
        # cursor.execute(sql_f1_check)
        # done_check = cursor.fetchall()
        # db.commit()
        # if len(done_check) > 0:
        #     if float(done_check[0][4]) < 0.5:
        #         print('F1 Warning !!')
        #         continue

        trade_operator.buy(stock_new[stock_index], state_dt, poz[stock_index] * deal_buy.cur_money_rest)
        del deal_buy
