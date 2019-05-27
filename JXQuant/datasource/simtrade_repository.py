from datasource import mysql

db = mysql.new_db()


def init_simtrade_data():
    """先清空之前的测试记录"""
    sql_delete_my_capital = 'delete from my_capital where seq != 1'
    db.delete(sql_delete_my_capital)

    sql_truncate_my_stock_pool = 'truncate table my_stock_pool'
    db.execute(sql_truncate_my_stock_pool)

    sql_truncate_model_ev_resu = 'truncate table model_ev_resu'
    db.execute(sql_truncate_model_ev_resu)

    sql_truncate_model_ev_mid = 'truncate table model_ev_mid'
    db.execute(sql_truncate_model_ev_mid)
