from datasource import mysql


class CurrentAccount(object):
    """模拟交易-当前最新的资金账户"""
    cur_capital = 0.00
    cur_money_lock = 0.00
    cur_money_rest = 0.00
    stock_pool = []
    stock_buyprice = {}
    stock_hold_volumn = {}
    stock_hold_days = {}
    stock_all = []
    ban_list = []

    def __init__(self, state_dt):
        try:
            db = mysql.new_db()
            sql_select_capital = 'select capital, money_lock, money_rest from my_capital a order by seq desc limit 1'
            last_capital_record = db.select_one(sql_select_capital)

            self.cur_capital = 0.00
            self.cur_money_lock = 0.00
            self.cur_money_rest = 0.00
            if last_capital_record is not None:
                self.cur_capital = float(last_capital_record[0])  # 总资产
                self.cur_money_rest = float(last_capital_record[2])  # 现金资产

            sql_select_stock_pool = 'select stock_code, buy_price, hold_vol, hold_days from my_stock_pool'
            stock_pool_records = db.select(sql_select_stock_pool)

            self.stock_pool = []
            self.stock_all = []
            self.stock_buyprice = []
            self.stock_hold_volumn = []
            self.stock_hold_days = []
            self.ban_list = []
            if len(stock_pool_records) > 0:
                self.stock_pool = [x[0] for x in stock_pool_records if x[2] > 0]
                self.stock_all = [x[0] for x in stock_pool_records]
                self.stock_buyprice = {x[0]: float(x[1]) for x in stock_pool_records}
                self.stock_hold_volumn = {x[0]: int(x[2]) for x in stock_pool_records}
                self.stock_hold_days = {x[0]: int(x[3]) for x in stock_pool_records}
            for i in range(len(stock_pool_records)):
                sql = "select close from stock_daily a where a.ts_code = %s and a.trade_date = %s limit 1"
                stock_close_record = db.select_one(sql, (stock_pool_records[i][0], state_dt))

                self.cur_money_lock += float(stock_close_record[0]) * float(stock_pool_records[i][2])
        except Exception as ex:
            print("Deal Error ", ex.args)
