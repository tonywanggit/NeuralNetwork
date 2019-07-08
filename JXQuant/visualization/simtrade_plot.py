from datasource import mysql
from pylab import *

db = mysql.new_db()


def plot_capital_profit(start_date, end_date):
    """回测结果可视化"""

    # 绘制大盘收益曲线
    sql_show_btc = "select state_dt, close from stock_index where stock_code = 'SH' and state_dt between %s and %s " \
                   "order by state_dt asc"
    show_btc_records = db.select(sql_show_btc, (start_date, end_date))
    btc_x = list(range(len(show_btc_records)))
    base_btc_close_price = show_btc_records[0][1]  # 投资周期开始时候的大盘收盘价
    btc_y = [x[1] / base_btc_close_price for x in show_btc_records]
    dict_anti_x = {}
    dict_x = {}
    for a in range(len(btc_x)):
        dict_anti_x[btc_x[a]] = show_btc_records[a][0]
        dict_x[show_btc_records[a][0]] = btc_x[a]

    # 绘制投资收益曲线
    sql_show_profit = "select max(capital), state_dt from my_capital " \
                      "where state_dt is not null group by state_dt order by state_dt asc"
    show_profit_records = db.select(sql_show_profit)
    profit_x = [dict_x[x[1]] for x in show_profit_records]
    profit_y = [x[0] / show_profit_records[0][0] for x in show_profit_records]

    # 绘制收益率曲线（含大盘基准收益曲线）
    def c_fnx(val, poz):
        if val in dict_anti_x.keys():
            return dict_anti_x[val]
        else:
            return ''

    fig = plt.figure()
    ax = fig.add_subplot(211)
    ax.xaxis.set_major_formatter(FuncFormatter(c_fnx))

    plt.plot(btc_x, btc_y, color='blue')
    plt.plot(profit_x, profit_y, color='red')
    plt.show()
