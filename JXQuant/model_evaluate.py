import datetime as dt
from sklearn import svm
import data_collector
import mysql
import multiprocessing as mp
from tushare_pro import build_test_date_seq

db = mysql.new_db()

# 模型评估时间窗口（单位：天）
MODEL_EVALUATE_DAYS = 90

# 数据集时间跨度（单位：天）
DATA_COLLECT_DAYS = 365


def model_eva_multi_process(stock_pool, predict_date):
    """模型评估一组股票，每支股票独立一个进程"""
    truncate_model_ev_mid()  # 清空中间表

    process_pool = []
    for stock in stock_pool:
        process = mp.Process(target=model_eva, args=(stock, predict_date, MODEL_EVALUATE_DAYS, DATA_COLLECT_DAYS))
        process.daemon = True
        process_pool.append(process)

    for p in process_pool:
        p.start()
    for p in process_pool:
        p.join()


def model_eva_single_process(stock_pool, predict_date):
    """模型评估一组股票"""
    truncate_model_ev_mid()  # 清空中间表

    for stock in stock_pool:
        model_eva(stock, predict_date, MODEL_EVALUATE_DAYS, DATA_COLLECT_DAYS)


def model_eva(stock, predict_date, model_ev_window, data_collect_window):
    """模型评估主函数"""

    # 构建模型评估时间序列
    model_eva_date_seq = build_test_date_seq(predict_date, model_ev_window)
    # truncate_model_ev_mid(stock)  # 清空评估用的中间表model_ev_mid 放到循环外部

    # 开始回测，其中data_collect_window参数代表建模时数据预处理所需的时间窗长度
    return_flag = execute_and_record_model_predict(stock, model_eva_date_seq, data_collect_window)
    if return_flag == 1:
        return -1
    else:
        # 计算实际结果并与预测值比较，根据比较结果给模型评分并记录结果
        calc_and_record_real_result(stock, model_eva_date_seq)
        calc_and_record_model_evaluate(stock, predict_date, model_eva_date_seq)
    return 1


def truncate_model_ev_mid():
    """清空模型评估中间数据"""

    sql_truncate_model_ev_mid = 'truncate table model_ev_mid'
    db.execute(sql_truncate_model_ev_mid)


def execute_and_record_model_predict(stock, date_seq, dc_days):
    """执行并记录模型预测结果"""
    for d in range(len(date_seq)):
        dc_end_date = date_seq[d]
        dc_start_date = (dt.datetime.strptime(dc_end_date, '%Y%m%d') - dt.timedelta(days=dc_days)).strftime('%Y%m%d')
        try:
            dc = data_collector.DataCollector(stock, dc_start_date, dc_end_date)
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
        model = svm.SVC(gamma='auto')
        model.fit(train, target)
        predict_result = model.predict(test_case)

        # 将预测结果插入到中间表
        sql_insert = "insert into model_ev_mid(state_dt, stock_code, resu_predict) values (%s, %s, %s)"
        db.insert(sql_insert, (dc_end_date, stock, round(float(predict_result[0]), 2)))
    return 0


def calc_and_record_real_result(stock, date_seq):
    """计算并记录真实的结果"""
    for i in range(len(date_seq)):
        sql_select = "select close from stock_daily a " \
                     "where a.ts_code = %s and a.trade_date <= %s order by a.trade_date desc limit 2"
        stock_daily_records = db.select(sql_select, (stock, date_seq[i]))

        if len(stock_daily_records) <= 1:
            break

        real_result = 0
        if float(stock_daily_records[0][0]) / float(stock_daily_records[1][0]) > 1.00:
            real_result = 1
        sql_update = "update model_ev_mid set resu_real = %s where state_dt = %s and stock_code = %s"
        db.update(sql_update, (real_result, date_seq[i], stock))


def calc_and_record_model_evaluate(stock_code, state_dt, date_seq):
    """计算并记录模型评估结果"""

    # 计算查全率
    sql_recall_son = "select count(*) from model_ev_mid " \
                     "where resu_real is not null and resu_predict = 1 and resu_real = 1 and stock_code=%s"
    predict_true_record = db.select_one(sql_recall_son, stock_code)
    predict_true_sample = predict_true_record[0]

    sql_recall_mon = "select count(*) from model_ev_mid a where a.resu_real is not null and a.resu_real = 1 " \
                     "and stock_code=%s"
    recall_mon_record = db.select_one(sql_recall_mon, stock_code)
    recall_mon = recall_mon_record[0]
    if recall_mon == 0:
        acc = recall = acc_neg = f1 = 0
    else:
        recall = predict_true_sample / recall_mon

    # 计算查准率
    sql_acc_mon = "select count(*) from model_ev_mid a where a.resu_real is not null and a.resu_predict = 1 " \
                  "and stock_code=%s"
    acc_mon_record = db.select_one(sql_acc_mon, stock_code)
    acc_mon = acc_mon_record[0]
    if acc_mon == 0:
        acc = recall = acc_neg = f1 = 0
    else:
        acc = predict_true_sample / acc_mon

    # 计算查准率(负样本)
    sql_acc_neg_son = "select count(*) from model_ev_mid " \
                      "where resu_real is not null and resu_predict = 0 and resu_real = 0 and stock_code=%s"
    acc_neg_son_record = db.select_one(sql_acc_neg_son, stock_code)
    acc_neg_son = acc_neg_son_record[0]

    sql_acc_neg_mon = "select count(*) from model_ev_mid where resu_real is not null and resu_predict = 0 " \
                      "and stock_code=%s"
    acc_neg_mon_record = db.select_one(sql_acc_neg_mon, stock_code)
    acc_neg_mon = acc_neg_mon_record[0]
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
    sql_predict = "select resu_predict from model_ev_mid where state_dt = %s and stock_code=%s limit 1"
    predict_record = db.select_one(sql_predict, (date_seq[-1], stock_code))

    predict = 0
    if predict_record is not None:
        predict = int(predict_record[0])

    # 将评估结果存入结果表model_ev_resu中
    sql_final_insert = "insert into model_ev_resu(state_dt, stock_code, acc,recall, f1, acc_neg, bz, predict)" \
                       "values(%s, %s, %s, %s, %s, %s, %s, %s)"
    db.insert(sql_final_insert, (state_dt, stock_code, round(acc, 4), round(recall, 4), round(f1, 4), round(acc_neg, 4)
                                 , 'svm', str(predict)))

    print(state_dt + '  ' + stock_code + '   Predict : ' + str(predict) + '   Precision : ' + str(acc) + '   Recall : '
          + str(recall) + '   F1 : ' + str(f1) + '   Acc_Neg : ' + str(acc_neg))
