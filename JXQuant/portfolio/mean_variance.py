import copy
import numpy as np
from datasource import mysql
from datasource.tushare_pro import build_test_date_seq

db = mysql.new_db()


def get_portfolio(stock_list, state_dt, para_window):
    """获取投资组合

    返回的resu中 特征值按由小到大排列，对应的是其特征向量
    """

    # 建评估时间序列, para_window参数代表回测窗口长度
    model_test_date_seq = build_test_date_seq(state_dt, para_window)

    list_return = []
    for i in range(len(model_test_date_seq) - 4):
        ri = []
        for j in range(len(stock_list)):
            sql_select = "select close from stock_daily where ts_code = %s and trade_date >= %s and trade_date <= %s " \
                         "order by trade_date asc"
            stock_daily_rs = db.select(sql_select, (stock_list[j], model_test_date_seq[i], model_test_date_seq[i + 4]))
            close_price = [x[0] for x in stock_daily_rs]
            base_price = 0.00
            after_mean_price = 0.00
            if len(close_price) <= 1:
                r = 0.00
            else:
                base_price = close_price[0]
                after_mean_price = np.array(close_price[1:]).mean()
                r = (float(after_mean_price / base_price) - 1.00) * 100.00
            ri.append(r)
            del stock_daily_rs
            del close_price
            del base_price
            del after_mean_price
        list_return.append(ri)

    # 求协方差矩阵
    cov = np.cov(np.array(list_return).T)

    # 求特征值和其对应的特征向量
    ans = np.linalg.eig(cov)

    # 排序，特征向量中负数置0，非负数归一
    ans_index = copy.copy(ans[0])
    ans_index.sort()
    resu = []
    for k in range(len(ans_index)):
        con_temp = []
        con_temp.append(ans_index[k])
        content_temp1 = ans[1][np.argwhere(ans[0] == ans_index[k])[0][0]]
        content_temp2 = []
        content_sum = np.array([x for x in content_temp1 if x >= 0.00]).sum()
        for m in range(len(content_temp1)):
            if content_temp1[m] >= 0 and content_sum > 0:
                content_temp2.append(content_temp1[m] / content_sum)
            else:
                content_temp2.append(0.00)
        con_temp.append(content_temp2)

        # 计算夏普率
        sharp_temp = np.array(copy.copy(list_return)) * content_temp2
        sharp_exp = sharp_temp.mean()
        sharp_base = 0.04
        sharp_std = np.std(sharp_temp)

        if sharp_std == 0.00:
            sharp = 0.00
        else:
            sharp = (sharp_exp - sharp_base) / sharp_std

        con_temp.append(sharp)
        resu.append(con_temp)
    return resu


def get_sharp_rate():
    """计算夏普率"""

    sql_capital = "select capital from my_capital a order by seq asc"
    capital_records = db.select(sql_capital)
    capital_list = [float(x[0]) for x in capital_records]
    return_list = []
    init_capital = float(capital_records[0][0])  # 初始资金
    for i in range(len(capital_list)):
        if i == 0:
            return_list.append(float(1.00))
        else:
            ri = (float(capital_records[i][0]) - init_capital) / init_capital
            return_list.append(ri)

    std = float(np.array(return_list).std())
    exp_portfolio = (float(capital_records[-1][0]) - init_capital) / init_capital
    exp_norisk = 0.04 * (5.0 / 12.0)
    sharp_rate = (exp_portfolio - exp_norisk) / std

    return sharp_rate, std

if __name__ == '__main__':
    pf = ['603912.SH', '300666.SZ', '300618.SZ', '002049.SZ', '300672.SZ']
    ans = get_portfolio(pf, '20180101', 90)

    print('**************  Market Trend  ****************')
    print('Risk : ' + str(round(ans[0][0], 2)))
    print('Sharp ratio : ' + str(round(ans[0][2], 2)))

    for i in range(5):
        print('----------------------------------------------')
        print('Stock_code : ' + str(pf[i]) + '  Position : ' + str(round(ans[0][1][i] * 100, 2)) + '%')
    print('----------------------------------------------')

    print('**************  Best Return  *****************')
    print('Risk : ' + str(round(ans[1][0], 2)))
    print('Sharp ratio : ' + str(round(ans[1][2], 2)))
    for j in range(5):
        print('----------------------------------------------')
        print('Stock_code : ' + str(pf[j]) + '  Position : ' + str(
            round(ans[1][1][j] * 100, 2)) + '%')
    print('----------------------------------------------')
