from pylab import *

import daily_execute_operator
import daily_update_capital as cap_update
import model_evaluate as ev
import mysql
import portfolio as pf
from tushare_pro import get_trade_date_seq

db = mysql.new_db()


def init_test_data():
    """先清空之前的测试记录"""
    sql_delete_my_capital = 'delete from my_capital where seq != 1'
    db.delete(sql_delete_my_capital)

    sql_truncate_my_stock_pool = 'truncate table my_stock_pool'
    db.execute(sql_truncate_my_stock_pool)

    sql_truncate_model_ev_resu = 'truncate table model_ev_resu'
    db.execute(sql_truncate_model_ev_resu)

    sql_truncate_model_ev_mid = 'truncate table model_ev_mid'
    db.execute(sql_truncate_model_ev_mid)


def loopback_testing(stock_pool, loopback_date_seq):
    """执行回测序列"""

    # 每日推进式建模，并获取对下一个交易日的预测结果
    for day_index in range(1, len(loopback_date_seq)):
        for stock in stock_pool:
            try:
                ev.model_eva(stock, loopback_date_seq[day_index], 90, 365)
            except Exception as ex:
                logging.exception("main exeute model evaluate fail", ex)
                continue

        # 每5个交易日更新一次配仓比例
        if divmod(day_index + 4, 5)[1] == 0:
            portfolio_pool = stock_pool
            if len(portfolio_pool) < 5:
                print('Less than 5 stocks for portfolio!! state_dt : ' + str(loopback_date_seq[day_index]))
                continue

            # 取最佳收益方向的资产组合
            pf_src = pf.get_portfolio(portfolio_pool, loopback_date_seq[day_index - 1], 90)
            weight = pf_src[1][1]
            daily_execute_operator.operate_stock(portfolio_pool, loopback_date_seq[day_index], loopback_date_seq[day_index - 1], weight)
        else:
            daily_execute_operator.operate_stock([], loopback_date_seq[day_index], loopback_date_seq[day_index - 1], [])
            cap_update.cap_update_daily(loopback_date_seq[day_index])

        print('Runnig to Date :  ' + str(loopback_date_seq[day_index]))


def get_sharp_rate():
    """计算夏普率"""

    sql_capital = "select * from my_capital a order by seq asc"
    capital_records = db.select(sql_capital)
    cap_list = [float(x[0]) for x in capital_records]
    return_list = []
    base_cap = float(capital_records[0][0])
    for i in range(len(cap_list)):
        if i == 0:
            return_list.append(float(1.00))
        else:
            ri = (float(capital_records[i][0]) - float(capital_records[0][0])) / float(capital_records[0][0])
            return_list.append(ri)
    std = float(np.array(return_list).std())
    exp_portfolio = (float(capital_records[-1][0]) - float(capital_records[0][0])) / float(capital_records[0][0])
    exp_norisk = 0.04 * (5.0 / 12.0)
    sharp_rate = (exp_portfolio - exp_norisk) / (std)

    return sharp_rate, std


def plot_capital_profit(start_date, end_date):
    """回测结果可视化"""

    # 绘制大盘收益曲线
    sql_show_btc = "select * from stock_index where stock_code = 'SH' and state_dt >= %s and state_dt <= %s " \
                   "order by state_dt asc"
    show_btc_records = db.select(sql_show_btc, (start_date, end_date))
    # btc_x = [x[0] for x in show_btc_records]
    btc_x = list(range(len(show_btc_records)))
    btc_y = [x[3] / show_btc_records[0][3] for x in show_btc_records]
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

    fig = plt.figure(figsize=(20, 12))
    ax = fig.add_subplot(111)
    ax.xaxis.set_major_formatter(FuncFormatter(c_fnx))

    plt.plot(btc_x, btc_y, color='blue')
    plt.plot(profit_x, profit_y, color='red')
    plt.show()


if __name__ == '__main__':
    year = 2018
    date_seq_start = str(year) + '0301'
    date_seq_end = str(year) + '0401'
    stock_pool = ['603912.SH', '300666.SZ', '300618.SZ', '002049.SZ', '300672.SZ']

    # 先清空之前的投资记录和持仓股票
    init_test_data()

    # 构建回测时间序列
    date_seq = get_trade_date_seq(date_seq_start, date_seq_end)
    print(date_seq)

    # 开始模拟交易
    loopback_testing(stock_pool, date_seq)
    print('ALL FINISHED!!')

    # 计算夏普率
    sharp, c_std = get_sharp_rate()
    print('Sharp Rate : ' + str(sharp))
    print('Risk Factor : ' + str(c_std))

    # 回测结果可视化
    plot_capital_profit(date_seq_start, date_seq_end)
