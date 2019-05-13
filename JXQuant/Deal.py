import pymysql.cursors


class Deal(object):
    """模拟交易-资金账户"""
    cur_capital = 0.00
    cur_money_lock = 0.00
    cur_money_rest = 0.00
    stock_pool = []
    stock_map_buyprice = {}
    stock_map_hold_volumn = {}
    stock_map_hold_days = {}
    stock_all = []
    ban_list = []

    def __init__(self, state_dt):
        # 建立数据库连接
        db = pymysql.connect(host='172.16.100.173', port=3306, user='root', passwd='111111', db='neuralnetwork',
                             charset='utf8')
        cursor = db.cursor()
        try:
            sql_select_capital = 'select capital, money_lock, money_rest from my_capital a order by seq desc limit 1'
            cursor.execute(sql_select_capital)
            done_set_capital = cursor.fetchall()
            self.cur_capital = 0.00
            self.cur_money_lock = 0.00
            self.cur_money_rest = 0.00
            if len(done_set_capital) > 0:
                self.cur_capital = float(done_set_capital[0][0])        # 总资产
                self.cur_money_rest = float(done_set_capital[0][2])     # 现金资产

            sql_select_stock_pool = 'select stock_code, buy_price, hold_vol, hod_days from my_stock_pool'
            cursor.execute(sql_select_stock_pool)
            done_set_stock_pool = cursor.fetchall()
            self.stock_pool = []
            self.stock_all = []
            self.stock_map_buyprice = []
            self.stock_map_hold_volumn = []
            self.stock_map_hold_days = []
            self.ban_list = []
            if len(done_set_stock_pool) > 0:
                self.stock_pool = [x[0] for x in done_set_stock_pool if x[2] > 0]
                self.stock_all = [x[0] for x in done_set_stock_pool]
                self.stock_map_buyprice = {x[0]: float(x[1]) for x in done_set_stock_pool}
                self.stock_map_hold_volumn = {x[0]: int(x[2]) for x in done_set_stock_pool}
                self.stock_map_hold_days = {x[0]: int(x[3]) for x in done_set_stock_pool}
            for i in range(len(done_set_stock_pool)):
                sql = "select close from stock_daily a where a.ts_code = '%s' and a.trade_date = '%s'" % (
                    done_set_stock_pool[i][0], state_dt)
                cursor.execute(sql)
                done_stock_daily = cursor.fetchall()
                db.commit()
                self.cur_money_lock += float(done_stock_daily[0][0]) * float(done_set_stock_pool[i][2])
        except Exception as excp:
            # db.rollback()
            print(excp)
        db.close()
