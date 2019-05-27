import datetime

from portfolio.mean_variance import get_sharp_rate
from simtrade.simtrade_main import loopback_testing
from visualization.simtrade_plot import plot_capital_profit

if __name__ == '__main__':
    year = 2018
    date_seq_start = str(year) + '0301'
    date_seq_end = str(year) + '0401'
    stock_pool = ['603912.SH', '300666.SZ', '300618.SZ', '002049.SZ', '300672.SZ']

    # 开始回测、模拟交易
    start_time = datetime.datetime.now()
    loopback_testing(stock_pool, date_seq_start, date_seq_end)
    end_time = datetime.datetime.now()
    print('模型回测耗时: ', (end_time - start_time).seconds)

    # 计算夏普率
    sharp, c_std = get_sharp_rate()
    print('Sharp Rate : ' + str(sharp))
    print('Risk Factor : ' + str(c_std))

    # 回测结果可视化
    plot_capital_profit(date_seq_start, date_seq_end)
