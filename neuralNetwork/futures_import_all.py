# -*- coding: utf-8 -*-
# @Time    : 2019/6/24 8:22
# @Author  : Tony
"""新版的期货数据导入接口"""

import tushare as ts
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

db = create_engine('mysql+pymysql://root:111111@172.16.100.173:3306/neuralnetwork?charset=utf8')
DBSession = sessionmaker(bind=db)

ts.set_token('22921f78f4ed876f539661a6a4ea58a4587da81d1c1523b95862dd3f')
pro = ts.pro_api()

daily = pro.fut_basic(exchange="INE")

print(daily.shape[0])
print(daily)
daily.to_sql('future_basic', db, index=False, if_exists='append')