import numpy as np
import datetime
import pymysql
import copy
import tushare as ts


def get_portfolio(stock_list, state_dt, para_window, db, cursor, ts_pro):
    """获取投资组合

    返回的resu中 特征值按由小到大排列，对应的是其特征向量
    """

    portfilio = stock_list

    # 建评估时间序列, para_window参数代表回测窗口长度
    model_test_date_start = (
            datetime.datetime.strptime(state_dt, '%Y%m%d') - datetime.timedelta(days=para_window)).strftime(
        '%Y%m%d')
    model_test_date_end = state_dt
    df = ts_pro.trade_cal(exchange_id='', is_open=1, start_date=model_test_date_start, end_date=model_test_date_end)
    model_test_date_seq = list(df.iloc[:, 1])

    list_return = []
    for i in range(len(model_test_date_seq) - 4):
        ri = []
        for j in range(len(portfilio)):
            sql_select = "select close from stock_daily a " \
                         "where a.ts_code = '%s' and a.trade_date >= '%s' and a.trade_date <= '%s' " \
                         "order by trade_date asc" % (portfilio[j], model_test_date_seq[i], model_test_date_seq[i + 4])
            cursor.execute(sql_select)
            done_set = cursor.fetchall()
            db.commit()
            close_price = [x[0] for x in done_set]
            base_price = 0.00
            after_mean_price = 0.00
            if len(close_price) <= 1:
                r = 0.00
            else:
                base_price = close_price[0]
                after_mean_price = np.array(close_price[1:]).mean()
                r = (float(after_mean_price / base_price) - 1.00) * 100.00
            ri.append(r)
            del done_set
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


if __name__ == '__main__':
    db = pymysql.connect(host='172.16.100.173', port=3306, user='root', passwd='111111', db='neuralnetwork',
                         charset='utf8')
    cursor = db.cursor()
    ts.set_token('17642bbd8d39b19c02cdf56002196c8709db65ce14ee62e08935ab0c')
    pro = ts.pro_api()

    pf = ['603912.SH', '300666.SZ', '300618.SZ', '002049.SZ', '300672.SZ']
    ans = get_portfolio(pf, '20180101', 90, db, cursor, pro)
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
