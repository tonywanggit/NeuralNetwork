from datasource.simtrade_repository import init_simtrade_data
from datasource.tushare_pro import get_trade_date_seq
from portfolio import mean_variance as pf
from predict import model_evaluate as ev
from quant_config import MODEL_EVALUATE_DAYS
from simtrade import daily_execute_operator, daily_update_capital as cap_update


def loopback_testing(stock_pool, start_dt, end_dt):
    """执行回测序列"""

    # 先清空之前的投资记录和持仓股票
    init_simtrade_data()

    # 构建回测时间序列
    loopback_date_seq = get_trade_date_seq(start_dt, end_dt)
    print(loopback_date_seq)

    # 每日推进式建模，并获取对下一个交易日的预测结果
    for day_index in range(1, len(loopback_date_seq)):
        ev.model_eva_multi_process(stock_pool, loopback_date_seq[day_index])

        # 每5个交易日更新一次配仓比例
        if divmod(day_index + 4, 5)[1] == 0:
            portfolio_pool = stock_pool
            if len(portfolio_pool) < 5:
                print('Less than 5 stocks for portfolio!! state_dt : ' + str(loopback_date_seq[day_index]))
                continue

            # 取最佳收益方向的资产组合
            pf_src = pf.get_portfolio(portfolio_pool, loopback_date_seq[day_index - 1], MODEL_EVALUATE_DAYS)
            weight = pf_src[1][1]
            daily_execute_operator.operate_stock(portfolio_pool, weight, loopback_date_seq[day_index],
                                                 loopback_date_seq[day_index - 1])
            cap_update.cap_update_daily(loopback_date_seq[day_index])
        else:
            daily_execute_operator.operate_stock([], [], loopback_date_seq[day_index], loopback_date_seq[day_index - 1])
            cap_update.cap_update_daily(loopback_date_seq[day_index])

        print('Runnig to Date :  ' + str(loopback_date_seq[day_index]))
