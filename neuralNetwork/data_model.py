from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from datetime import timedelta

# 创建对象的基类:
Base = declarative_base()


class StockInfo(Base):
    # 表的名字:
    __tablename__ = 'stock_basic'

    # 表的结构：
    ts_code = Column(String(50), primary_key=True)
    symbol = Column(String(50))
    name = Column(String(50))
    area = Column(String(50))
    industry = Column(String(50))
    market = Column(String(50))
    list_date = Column(String(50))
    update_date = Column(String(50))

    def __repr__(self):
        return '%s(%r)(%r)' % (self.__class__.__name__, self.ts_code, self.update_date)


if __name__ == '__main__':
    db = create_engine('mysql+pymysql://root:111111@172.16.100.173:3306/neuralnetwork?charset=utf8')
    DBSession = sessionmaker(bind=db)
    session = DBSession()
    # stock_info = session.query(StockInfo).filter(StockInfo.ts_code == '000001.SZ').one()
    stock_info = StockInfo(ts_code='000001.SZ', update_date=datetime.today().strftime('%Y%m%d'))
    session.merge(stock_info)
    session.commit()
    stock_info = session.query(StockInfo).filter(StockInfo.ts_code == '000001.SZ').one()
    session.close()
    print(stock_info)
