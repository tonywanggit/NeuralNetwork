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

    db = create_engine('mysql+pymysql://root:111111@172.16.100.173:3306/neuralnetwork?charset=utf8')
    sql_cmd = 'select open, close, high, low from stock_basic order by trade_date asc limit %d' % input_day
    df = pd.read_sql(sql=sql_cmd, con=db)

    print(df)
    print(df[2:4])

    neuralNetwork = NeuralNetwork(input_nodes, hidden_nodes, output_nodes, learning_rate)
    print("run nerual network")
