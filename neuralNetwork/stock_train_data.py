import pandas as pd
import numpy as np
import scipy
from sqlalchemy import create_engine

from neuralNetwork.neural_network import NeuralNetwork

input_days = 5  # 取5天前的数据，预测2天后的最高值
target_days = 2
input_nodes = input_days * 4  # 输入节点 = 输入天数 * 每天的数据量
hidden_nodes = 100
output_nodes = 1
learning_rate = 0.2
stock_max_row = 10000
neuralNetwork = NeuralNetwork(input_nodes, hidden_nodes, output_nodes, learning_rate)


def train(input_data, target_data, price_max):
    print(input_data)
    print(input_data[4:5]['close'])
    print(target_data)
    print(target_data['high'].max())

    last_close = input_data[input_days - 1:input_days]['close']
    high_max = target_data['high'].max()
    profit = high_max - last_close
    profit_max = last_close * 0.1 * target_days  # 每天最多盈利 10%
    target = profit / profit_max

    inputs = (np.asfarray(input_data.values).reshape(input_nodes) / price_max * 0.99) + 0.01
    targets = np.asfarray(scipy.special.expit(target))
    neuralNetwork.train(inputs, targets)
    return


if __name__ == '__main__':
    db = create_engine('mysql+pymysql://root:111111@172.16.100.173:3306/neuralnetwork?charset=utf8')
    sql_cmd = 'select open, close, high, low from stock_basic order by trade_date asc limit %d' % stock_max_row
    df = pd.read_sql(sql=sql_cmd, con=db)

    price_max = df['high'].max()
    data_size = df.size

    print()

    train(df[0:input_days], df[input_days:input_days + target_days], price_max)
