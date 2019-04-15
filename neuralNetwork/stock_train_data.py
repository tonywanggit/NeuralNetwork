import pandas as pd
import numpy as np
from sqlalchemy import create_engine

from neuralNetwork.neural_network import NeuralNetwork

if __name__ == '__main__':
    input_day = 5
    input_nodes = input_day * 4
    hidden_nodes = 100
    output_nodes = 1
    learning_rate = 0.2
    stock_max_row = 10000

    db = create_engine('mysql+pymysql://root:111111@172.16.100.173:3306/neuralnetwork?charset=utf8')
    sql_cmd = 'select open, close, high, low from stock_basic order by trade_date asc limit %d' % stock_max_row
    df = pd.read_sql(sql=sql_cmd, con=db)

    price_max = df['high'].max();
    # vol_max = df['vol'].max();
    # print(price_max, vol_max)

    print((np.asfarray(df[0:7].values).reshape(28) / price_max * 0.99) + 0.01)


    neuralNetwork = NeuralNetwork(input_nodes, hidden_nodes, output_nodes, learning_rate)
    print("run nerual network")
