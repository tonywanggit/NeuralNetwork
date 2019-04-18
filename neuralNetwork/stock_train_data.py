import pandas as pd
import numpy as np
import math
from sqlalchemy import create_engine

from neuralNetwork.neural_network import NeuralNetwork

input_days = 5  # 取5天前的数据
target_days = 2  # 预测2天后的最高值
test_days = 2  # 测试天数
input_nodes = input_days * 4  # 输入节点 = 输入天数 * 每天的数据量
hidden_nodes = 100
output_nodes = 1
learning_rate = 0.2
stock_max_row = 10000
neuralNetwork = NeuralNetwork(input_nodes, hidden_nodes, output_nodes, learning_rate)


def train(input_data, target_data, price_max):
    last_close = input_data[input_days - 1:input_days]['close'].astype(np.float)
    profit = target_data['high'].max() - last_close

    inputs = (np.asfarray(input_data.values).reshape(input_nodes) / price_max * 0.99) + 0.01
    outputs = np.asfarray(cal_output(profit, last_close))

    neuralNetwork.train(inputs, outputs)
    return


def query(input_data, target_data, price_max):
    print(input_data)
    print(target_data)

    inputs = (np.asfarray(input_data.values).reshape(input_nodes) / price_max * 0.99) + 0.01
    target_value = neuralNetwork.query(inputs)

    print(target_value)


def cal_output(profit, last_close):
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
    sql_cmd = 'select open, close, high, low from stock_basic order by trade_date asc limit %d' % stock_max_row
    df = pd.read_sql(sql=sql_cmd, con=db)

    high_max = df['high'].max()  # 全数据集的最高价
    train_times = df.shape[0] - input_days - target_days + 1 - test_days  # 计算训练次数
    if train_times <= 0:
        exit("not enough data")

    for i in range(0, train_times):
        train(df[i:input_days + i], df[input_days + i:input_days + target_days + i], high_max)

    for i in range(train_times, train_times + test_days):
        query(df[i:input_days + i], df[input_days + i:input_days + target_days + i], high_max)
