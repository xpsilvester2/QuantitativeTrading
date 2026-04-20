import matplotlib.pyplot as plt
import pandas as pd
import mplfinance as mpf
from unittest import TestCase


class TestPandasKLine(TestCase):
    #读取股票数据，画出K线图
    def testKLineChart(self):
        file_name = "./demo.csv"
        df = pd.read_csv(file_name, encoding='gbk')
        df.columns = ['stock_id','date', 'close', 'open', 'high', 'low', 'volume']
        
        # 将日期列设置为索引
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
                # 使用 mplfinance 绘制 K 线图
        # 自定义颜色（中国股市：红涨绿跌）
        mc = mpf.make_marketcolors(
            up='red',           # 上涨颜色
            down='green',       # 下跌颜色
            edge='inherit',     # 边框颜色继承 K 线颜色
            wick='inherit',     # 影线颜色继承 K 线颜色
            volume='inherit'    # 成交量颜色继承 K 线颜色
        )
        
        # 自定义样式
        s = mpf.make_mpf_style(
            marketcolors=mc,
            gridstyle='-',      # 网格线样式
            y_on_right=True     # Y 轴标签显示在右侧
        )
        
        mpf.plot(
            df,
            type='candle',           # K线类型
            style=s,                 # 自定义样式
            title='K-Line Chart',    # 标题
            ylabel='Price',          # Y轴标签
            ylabel_lower='Volume',   # 成交量 Y 轴标签
            volume=True,             # 显示成交量
            figsize=(10, 6),         # 图表大小
            mav=(5, 10)              # 移动平均线（5日和10日）
        )
        
        
if __name__ == '__main__':
    test = TestPandasKLine()
    test.testKLineChart()