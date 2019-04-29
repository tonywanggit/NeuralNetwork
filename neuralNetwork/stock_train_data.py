import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import math
from sqlalchemy import create_engine
from datetime import datetime
from neuralNetwork.neural_network import NeuralNetwork
from pandas.plotting import register_matplotlib_converters

register_matplotlib_converters()

input_days = 5  # 取5天前的数据
target_days = 2  # 预测2天后的最高值
test_days = 30  # 测试天数
oneday_dimensions = 5  # 每天的数据维度（open, close, high, low, vol）
input_nodes = input_days * oneday_dimensions  # 输入节点 = 输入天数 * 每天的数据量
hidden_nodes = 100
output_nodes = 1
learning_rate = 0.2
stock_max_row = 100000
ts_code = '002230.SZ'
neuralNetwork = NeuralNetwork(input_nodes, hidden_nodes, output_nodes, learning_rate)


def train(input_data, target_data, price_max, vol_max):
    inputs = [calc_input(x, price_max, vol_max) for x in np.asfarray(input_data.values).reshape(input_nodes)]
    outputs = np.asfarray(cal_output(input_data, target_data))

    neuralNetwork.train(inputs, outputs)
    return


def query(input_data, price_max, vol_max):
    inputs = [calc_input(x, price_max, vol_max) for x in np.asfarray(input_data.values).reshape(input_nodes)]
    target_value = neuralNetwork.query(inputs)

    return np.float(target_value[0])


def calc_input(input_value, price_max, vol_max):
    if input_value < price_max:
        return (input_value / (price_max + 0.01)) * 0.99 + 0.01
    else:
        return (input_value / (vol_max + 0.01)) * 0.99 + 0.01


def cal_output(input_data, target_data):
    last_close = input_data[input_days - 1:input_days]['close'].astype(np.float)
    profit = target_data['high'].max() - last_close
    profit_max = last_close * math.pow(1.1, target_days) - last_close  # 每天最多盈利 10%
    target = np.float(profit / profit_max)

    if target >= 1:
        return 0.99
    elif target <= -1:
        return 0.01
    else:
        return target * 0.5 + 0.5


if __name__ == '__main__':
    db = create_engine('mysql+pymysql://root:111111@172.16.100.173:3306/neuralnetwork?charset=utf8')
    sql_cmd = 'select open, close, high, low, vol from stock_daily where ts_code = %(ts_code)s order by trade_date asc'
    df = pd.read_sql(sql=sql_cmd, con=db, params={'ts_code': ts_code})

    sql_cmd_date = 'select trade_date from stock_daily where ts_code = %(ts_code)s order by trade_date asc'
    df_date = pd.read_sql(sql=sql_cmd_date, con=db, params={'ts_code': ts_code})

    high_max = df['high'].max()  # 全数据集的最高价
    vol_max = df['vol'].max()  # 全数据集的最高价
    train_times = df.shape[0] - input_days - target_days + 1 - test_days  # 计算训练次数
    if train_times <= 0:
        exit("not enough data")

    for i in range(0, train_times):
        train(df[i:input_days + i], df[input_days + i:input_days + target_days + i], high_max, vol_max)

    target_outputs = []
    predicted_outputs = []
    trade_dates = np.asanyarray(df_date[train_times + input_days - 1:train_times + input_days + test_days - 1])\
        .reshape(test_days)
    trade_dates = [datetime.strptime(str(m), '%Y%m%d').date() for m in trade_dates]
    for i in range(train_times, train_times + test_days):
        # print(df[i:input_days + i], df[input_days + i:input_days + target_days + i])
        predicted_outputs.append(query(df[i:input_days + i], high_max, vol_max))
        target_outputs.append(cal_output(df[i:input_days + i], df[input_days + i:input_days + target_days + i]))

    print(predicted_outputs)
    print(target_outputs)

    # 配置横坐标
    plt.figure()
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%Y'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator())

    plt.title(ts_code)
    plt.xlabel('Date')
    plt.ylabel('Profit')
    plt.plot(trade_dates, target_outputs)
    plt.plot(trade_dates, predicted_outputs, color='red', linewidth=1.0, linestyle='--')
    plt.gcf().autofmt_xdate()  # 自动旋转日期标记
    plt.show()
