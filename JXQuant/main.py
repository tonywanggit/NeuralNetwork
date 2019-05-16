import pymysql
import Model_Evaluate as ev
import Filter
import Portfolio as pf
from pylab import *
import Cap_Update_daily as cap_update
import tushare as ts

db = pymysql.connect(host='172.16.100.173', port=3306, user='root', passwd='111111', db='neuralnetwork',
                     charset='utf8')
cursor = db.cursor()
ts.set_token('17642bbd8d39b19c02cdf56002196c8709db65ce14ee62e08935ab0c')
pro = ts.pro_api()


def init_test_data():
    """先清空之前的测试记录"""
    sql_wash1 = 'delete from my_capital where seq != 1'
    cursor.execute(sql_wash1)
    db.commit()
    sql_wash3 = 'truncate table my_stock_pool'
    cursor.execute(sql_wash3)
    db.commit()
    # 清空行情源表，并插入相关股票的行情数据。该操作是为了提高回测计算速度而剔除行情表(stock_all)中的冗余数据。
    # sql_wash4 = 'truncate table stock_info'
    #     # cursor.execute(sql_wash4)
    #     # db.commit()
    # in_str = '('
    # for x in range(len(stock_pool)):
    #     if x != len(stock_pool) - 1:
    #         in_str += str('\'') + str(stock_pool[x]) + str('\',')
    #     else:
    #         in_str += str('\'') + str(stock_pool[x]) + str('\')')
    # sql_insert = "insert into stock_info(select * from stock_all a where a.stock_code in %s)" % (in_str)
    # cursor.execute(sql_insert)
    # db.commit()


def loopback_testing(stock_pool, test_date_seq):
    """执行回测序列"""

    day_index = 0
    for i in range(1, len(test_date_seq)):
        day_index += 1
        # 每日推进式建模，并获取对下一个交易日的预测结果
        for stock in stock_pool:
            try:
                ans2 = ev.model_eva(stock, test_date_seq[i], 90, 365, cursor, db)
                # print('Date : ' + str(date_seq[i]) + ' Update : ' + str(stock))
            except Exception as ex:
                print(ex)
                continue

        # 每5个交易日更新一次配仓比例
        if divmod(day_index + 4, 5)[1] == 0:
            portfolio_pool = stock_pool
            if len(portfolio_pool) < 5:
                print('Less than 5 stocks for portfolio!! state_dt : ' + str(test_date_seq[i]))
                continue
            pf_src = pf.get_portfolio(portfolio_pool, test_date_seq[i - 1], 90, db, cursor, pro)
            # 取最佳收益方向的资产组合
            risk = pf_src[1][0]
            weight = pf_src[1][1]
            Filter.filter_main(portfolio_pool, test_date_seq[i], test_date_seq[i - 1], weight, db)
        else:
            Filter.filter_main([], test_date_seq[i], test_date_seq[i - 1], [], db)
            cap_update_ans = cap_update.cap_update_daily(test_date_seq[i])
        print('Runnig to Date :  ' + str(test_date_seq[i]))


def get_sharp_rate():
    """计算夏普率"""

    sql_cap = "select * from my_capital a order by seq asc"
    cursor.execute(sql_cap)
    done_exp = cursor.fetchall()
    db.commit()
    cap_list = [float(x[0]) for x in done_exp]
    return_list = []
    base_cap = float(done_exp[0][0])
    for i in range(len(cap_list)):
        if i == 0:
            return_list.append(float(1.00))
        else:
            ri = (float(done_exp[i][0]) - float(done_exp[0][0])) / float(done_exp[0][0])
            return_list.append(ri)
    std = float(np.array(return_list).std())
    exp_portfolio = (float(done_exp[-1][0]) - float(done_exp[0][0])) / float(done_exp[0][0])
    exp_norisk = 0.04 * (5.0 / 12.0)
    sharp_rate = (exp_portfolio - exp_norisk) / (std)

    return sharp_rate, std


def plot_capital_profit(start_date, end_date):
    """回测结果可视化"""

    # 绘制大盘收益曲线
    sql_show_btc = "select * from stock_index a " \
                   "where a.stock_code = 'SH' and a.state_dt >= '%s' and a.state_dt <= '%s' " \
                   "order by state_dt asc" % (start_date, end_date)
    cursor.execute(sql_show_btc)
    done_set_show_btc = cursor.fetchall()
    # btc_x = [x[0] for x in done_set_show_btc]
    btc_x = list(range(len(done_set_show_btc)))
    btc_y = [x[3] / done_set_show_btc[0][3] for x in done_set_show_btc]
    dict_anti_x = {}
    dict_x = {}
    for a in range(len(btc_x)):
        dict_anti_x[btc_x[a]] = done_set_show_btc[a][0]
        dict_x[done_set_show_btc[a][0]] = btc_x[a]

    # 绘制投资收益曲线
    sql_show_profit = "select max(a.capital),a.state_dt from my_capital a " \
                      "where a.state_dt is not null group by a.state_dt order by a.state_dt asc"
    cursor.execute(sql_show_profit)
    done_set_show_profit = cursor.fetchall()
    profit_x = [dict_x[x[1]] for x in done_set_show_profit]
    profit_y = [x[0] / done_set_show_profit[0][0] for x in done_set_show_profit]

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

    # 先清空之前的测试记录,并创建中间表
    init_test_data()

    # 构建回测时间序列
    df = pro.trade_cal(exchange_id='', is_open=1, start_date=date_seq_start, end_date=date_seq_end)
    date_seq = list(df.iloc[:, 1])
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

    cursor.close()
    db.close()
