from sklearn import svm
import pymysql.cursors
import datetime
import DC
import tushare as ts


def model_eva(stock, state_dt, para_window, para_dc_window):
    """模型评估主函数"""
    db = pymysql.connect(host='172.16.100.173', port=3306, user='root', passwd='111111', db='neuralnetwork',
                         charset='utf8')
    cursor = db.cursor()

    # 构建回测时间序列
    model_test_date_seq = build_test_date_seq(state_dt, para_window)
    truncate_model_ev_mid(db, cursor)  # 清空评估用的中间表model_ev_mid

    # 开始回测，其中para_dc_window参数代表建模时数据预处理所需的时间窗长度
    return_flag = execute_and_record_model_predict(stock, para_dc_window, cursor, db)
    if return_flag == 1:
        return -1
    else:
        # 计算实际结果并与预测值比较，根据比较结果给模型评分并记录结果
        calc_and_record_real_result(stock, model_test_date_seq, cursor, db)
        calc_and_record_model_evaluate(stock, state_dt, model_test_date_seq, cursor, db)
    return 1


def build_test_date_seq(state_dt, para_window):
    """构建回测时间序列"""
    ts.set_token('17642bbd8d39b19c02cdf56002196c8709db65ce14ee62e08935ab0c')
    pro = ts.pro_api()
    # 建评估时间序列, para_window参数代表回测窗口长度
    model_test_date_start = (
            datetime.datetime.strptime(state_dt, '%Y%m%d') - datetime.timedelta(days=para_window)).strftime(
        '%Y%m%d')
    model_test_date_end = state_dt
    df = pro.trade_cal(exchange_id='', is_open=1, start_date=model_test_date_start, end_date=model_test_date_end)
    return list(df.iloc[:, 1])


def truncate_model_ev_mid(db, cursor):
    """清空模型评估中间数据"""
    sql_truncate_model_test = 'truncate table model_ev_mid'
    cursor.execute(sql_truncate_model_test)
    db.commit()


def execute_and_record_model_predict(stock, date_seq, dc_window, cursor, db):
    """执行并记录模型预测结果"""
    for d in range(len(date_seq)):
        model_test_new_start = (datetime.datetime.strptime(date_seq[d], '%Y%m%d') - datetime.timedelta(
            days=dc_window)).strftime('%Y%m%d')
        model_test_new_end = model_test_date_seq[d]
        try:
            dc = DC.data_collect(stock, model_test_new_start, model_test_new_end)
            if len(set(dc.data_target)) <= 1:
                continue
        except Exception as exp:
            print("DC Error", exp)
            return 1

        # 构建训练数据集合测试用例
        train = dc.data_train
        target = dc.data_target
        test_case = [dc.test_case]

        # 建模 训练 预测
        model = svm.SVC()
        model.fit(train, target)
        predict_result = model.predict(test_case)

        # 将预测结果插入到中间表
        sql_insert = "insert into model_ev_mid(state_dt,stock_code,resu_predict)values('%s','%s','%.2f')" % (
            model_test_new_end, stock, float(predict_result[0]))
        cursor.execute(sql_insert)
        db.commit()
        return 0


def calc_and_record_real_result(stock, date_seq, cursor, db):
    """计算并记录真实的结果"""
    for i in range(len(date_seq)):
        sql_select = "select close from stock_daily a " \
                     "where a.ts_code = '%s' and a.trade_date >= '%s' order by a.state_dt asc limit 2" % (
                         stock, date_seq[i])
        cursor.execute(sql_select)
        done_set2 = cursor.fetchall()
        if len(done_set2) <= 1:
            break
        real_result = 0
        if float(done_set2[1][0]) / float(done_set2[0][0]) > 1.00:
            real_result = 1
        sql_update = "update model_ev_mid w set w.resu_real = '%.2f' " \
                     "where w.state_dt = '%s' and w.stock_code = '%s'" % (
                         real_result, model_test_date_seq[i], stock)
        cursor.execute(sql_update)
        db.commit()


def calc_and_record_model_evaluate(stock, state_dt, date_seq, cursor, db):
    """计算并记录模型评估结果"""

    # 计算查全率
    sql_resu_recall_son = "select count(*) from model_ev_mid a " \
                          "where a.resu_real is not null and a.resu_predict = 1 and a.resu_real = 1"
    cursor.execute(sql_resu_recall_son)
    predict_true_sample = cursor.fetchall()[0][0]
    sql_resu_recall_mon = "select count(*) from model_ev_mid a where a.resu_real is not null and a.resu_real = 1"
    cursor.execute(sql_resu_recall_mon)
    recall_mon = cursor.fetchall()[0][0]
    if recall_mon == 0:
        acc = recall = acc_neg = f1 = 0
    else:
        recall = predict_true_sample / recall_mon

    # 计算查准率
    sql_resu_acc_mon = "select count(*) from model_ev_mid a where a.resu_real is not null and a.resu_predict = 1"
    cursor.execute(sql_resu_acc_mon)
    acc_mon = cursor.fetchall()[0][0]
    if acc_mon == 0:
        acc = recall = acc_neg = f1 = 0
    else:
        acc = predict_true_sample / acc_mon

    # 计算查准率(负样本)
    sql_resu_acc_neg_son = "select count(*) from model_ev_mid a " \
                           "where a.resu_real is not null and a.resu_predict = -1 and a.resu_real = -1"
    cursor.execute(sql_resu_acc_neg_son)
    acc_neg_son = cursor.fetchall()[0][0]
    sql_resu_acc_neg_mon = "select count(*) from model_ev_mid a " \
                           "where a.resu_real is not null and a.resu_predict = -1"
    cursor.execute(sql_resu_acc_neg_mon)
    acc_neg_mon = cursor.fetchall()[0][0]
    if acc_neg_mon == 0:
        acc_neg = -1
    else:
        acc_neg = acc_neg_son / acc_neg_mon

    # 计算 F1 分值
    if acc + recall == 0:
        acc = recall = acc_neg = f1 = 0
    else:
        f1 = (2 * acc * recall) / (acc + recall)

    # 取出评估日期当天的预测值
    sql_predict = "select resu_predict from model_ev_mid a where a.state_dt = '%s'" % (date_seq[-1])
    cursor.execute(sql_predict)
    done_predict = cursor.fetchall()
    predict = 0
    if len(done_predict) != 0:
        predict = int(done_predict[0][0])

    # 将评估结果存入结果表model_ev_resu中
    sql_final_insert = "insert into model_ev_resu(state_dt,stock_code,acc,recall,f1,acc_neg,bz,predict)" \
                       "values('%s','%s','%.4f','%.4f','%.4f','%.4f','%s','%s')" % \
                       (state_dt, stock, acc, recall, f1, acc_neg, 'svm', str(predict))
    cursor.execute(sql_final_insert)
    db.commit()
    db.close()
    print(str(state_dt) + '   Precision : ' + str(acc) + '   Recall : ' + str(recall) + '   F1 : ' + str(
        f1) + '   Acc_Neg : ' + str(acc_neg))


if __name__ == '__main__':
    ts.set_token('17642bbd8d39b19c02cdf56002196c8709db65ce14ee62e08935ab0c')
    pro = ts.pro_api()
    df = pro.trade_cal(exchange_id='', is_open=1, start_date='20190425', end_date='20190509')
    date_temp = list(df.iloc[:, 1])
    print(df)
    print(date_temp)
    # model_test_date_seq = [(datetime.datetime.strptime(x, "%Y%m%d")).strftime('%Y-%m-%d') for x in date_temp]
    # print(model_test_date_seq)
