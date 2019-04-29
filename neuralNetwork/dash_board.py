import matplotlib.pyplot as plt
import numpy as np

import pandas as pd
from sqlalchemy import create_engine


def trans_data(input_data):
    input_data[['vol', 'low']] = input_data[['vol', 'low']] * 100
    print(input_data)


def calc_input(input, price_max, vol_max):
    if input < price_max:
        return (input / (price_max + 0.01)) * 0.99 + 0.01
    else:
        return (input / (vol_max + 0.01)) * 0.99 + 0.01


ts_code = '000001.SZ'

db = create_engine('mysql+pymysql://root:111111@172.16.100.173:3306/neuralnetwork?charset=utf8')
sql_cmd = 'select open, close, high, low, vol from stock_daily where ts_code = %(ts_code)s order by trade_date asc limit 2'
df = pd.read_sql(sql=sql_cmd, con=db, params={'ts_code': ts_code})
print(df)

input_array = np.asfarray(df.values).reshape(10)
print(input_array)
# map(lambda x: calc_input(x, 12.9, 165283.74), input_array)
input_array = [calc_input(x, 12.9, 165283.74) for x in input_array]
print(input_array)
