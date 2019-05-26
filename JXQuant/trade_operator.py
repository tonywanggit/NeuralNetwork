import account
import mysql
from trade_config import *

"""模拟交易-操作模块"""


def buy(stock_code, opdate, buy_money):
    """模拟交易-买入操作"""
    db = mysql.new_db()
    deal_account = account.CurrentAccount(opdate)

    # 后买入
    if deal_account.cur_money_rest + 1 >= buy_money:
        sql_buy = "select close from stock_daily a where a.trade_date = %s and a.ts_code = %s"
        stock_close_record = db.select_one(sql_buy, (opdate, stock_code))
        if stock_close_record is None:
            return -1

        buy_price = float(stock_close_record[0])
        if buy_price >= MAX_BUY_PRICE_LIMIT:  # 最高成交价限额保护
            return 0

        # 计算出可以都买的股票数量
        vol, rest = divmod(min(deal_account.cur_money_rest, buy_money), buy_price * DEAL_MIN_VOLUMN)
        vol = vol * 100
        if vol == 0:
            return 0
        new_capital = float(deal_account.cur_capital - vol * buy_price * DEAL_COST_RATIO)  # 计算税后的总资产
        new_money_lock = float(deal_account.cur_money_lock + vol * buy_price)  # 计算股票资产
        new_money_rest = float(deal_account.cur_money_rest - vol * buy_price * (1 + DEAL_COST_RATIO))  # 计算现金资产

        # 添加一条投资记录
        sql_buy_stock = "insert into my_capital(capital, money_lock, money_rest, deal_action" \
                        ", stock_code, stock_vol, state_dt, deal_price, bz) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        db.insert(sql_buy_stock, (float(round(new_capital, 2)), round(new_money_lock, 2), round(new_money_rest, 2)
                                  , 'BUY', stock_code, int(vol), opdate, round(buy_price, 2), 'BUY'))

        if stock_code in deal_account.stock_all:
            # 计算加仓后的股票平均成本和最新的持仓量
            new_buy_price = (deal_account.stock_buyprice[stock_code] * deal_account.stock_hold_volumn[
                stock_code] + vol * buy_price) / (deal_account.stock_hold_volumn[stock_code] + vol)
            new_vol = deal_account.stock_hold_volumn[stock_code] + vol
            sql_buy_update = "update my_stock_pool set buy_price=%s, hold_vol=%s, hold_days=%s where stock_code=%s"
            db.update(sql_buy_update, (round(new_buy_price, 2), int(new_vol), 1))
        else:
            sql_buy_insert = "insert into my_stock_pool(stock_code,buy_price,hold_vol,hold_days) " \
                             "VALUES (%s, %s, %s, %s)"
            db.insert(sql_buy_insert, (stock_code, buy_price, int(vol), 1))
        return 1
    return 0


def sell(stock_code, opdate, predict):
    """模拟交易-卖出操作"""
    db = mysql.new_db()

    deal_account = account.CurrentAccount(opdate)
    buy_price = deal_account.stock_buyprice[stock_code]
    hold_vol = deal_account.stock_hold_volumn[stock_code]
    hold_days = deal_account.stock_hold_days[stock_code]

    sql_stock_close = "select close from stock_daily a where a.trade_date = %s and a.ts_code = %s"
    stock_close_record = db.select_one(sql_stock_close, (opdate, stock_code))
    if stock_close_record is None:
        return -1

    sell_price = float(stock_close_record[0])  # 以当日收盘价作为卖出价

    if sell_price > buy_price * 1.03 and hold_vol > 0:
        __sell_op(db, deal_account, stock_code, sell_price, buy_price, hold_vol, opdate, 'SELL', 'GOOD_SELL')
        return 1

    elif sell_price < buy_price * 0.97 and hold_vol > 0:
        __sell_op(db, deal_account, stock_code, sell_price, buy_price, hold_vol, opdate, 'SELL', 'BAD_SELL')
        return 1

    elif hold_days >= 4 and hold_vol > 0:
        __sell_op(db, deal_account, stock_code, sell_price, buy_price, hold_vol, opdate, 'SELL', 'OVERTIME_SELL')
        return 1

    elif predict == 0:
        __sell_op(db, deal_account, stock_code, sell_price, buy_price, hold_vol, opdate, 'SELL', 'PREDICT_SELL')
        return 1
    return 0


def __sell_op(db, deal_account, stock_code, sell_price, buy_price, hold_vol, opdate, deal_action, bz):
    new_money_lock = float(deal_account.cur_money_lock - sell_price * hold_vol)
    new_money_rest = float(deal_account.cur_money_rest + sell_price * hold_vol)
    new_capital = float(deal_account.cur_capital + (sell_price - buy_price) * hold_vol)
    new_profit = float((sell_price - buy_price) * hold_vol)
    new_profit_rate = float(sell_price / buy_price)

    # 添加一条投资记录(卖出股票)
    sql_sell_stock = "insert into my_capital(capital, money_lock, money_rest, deal_action" \
                     ", stock_code, stock_vol, profit, profit_rate, bz, state_dt, deal_price) " \
                     "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    db.insert(sql_sell_stock, (round(new_capital, 2), round(new_money_lock, 2), round(new_money_rest, 2)
                               , deal_action, stock_code, int(hold_vol), round(new_profit, 2), round(new_profit_rate, 2)
                               , bz, opdate, round(sell_price, 2)))

    sql_delete_stock = "delete from my_stock_pool where stock_code = %s"
    db.delete(sql_delete_stock, (stock_code))
