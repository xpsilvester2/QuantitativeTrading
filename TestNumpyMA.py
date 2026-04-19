import numpy as np
import matplotlib.pyplot as plt

from unittest import TestCase


class TestNumpyMA(TestCase):

    def testSMA(self):
        file_name = "./demo.csv"
        end_price = np.loadtxt(
            fname=file_name,
            delimiter=',',
            usecols=(2),
            unpack=True,
            skiprows=1
        )
        print(end_price)
        
        # 计算简单移动平均（SMA）
        # 使用卷积计算5日移动平均
        N = 5
        weights = np.ones(N) / N
        print(weights)
        sma = np.convolve(weights,end_price)[N-1:-N+1]
        print(sma)
        plt.plot(sma,linewidth=5)
        plt.show()

    def testEXP(self):
        x = np.arange(5)
        y = np.arange(10)
        print("x", x)  # exp 函数可以计算出每个数组元素的指数
        print("y", y)
        print("""Exp x : {}""".format(np.exp(x)))
        print("""Exp y : {}""".format(np.exp(y)))
        print("""Linespace : {}""".format(np.linspace(-1, 0, 5)))

    def testEMA(self):
        file_name = "./demo.csv"
        end_price = np.loadtxt(
            fname=file_name,
            delimiter=',',
            usecols=(2),
            unpack=True,
            skiprows=1
        )
        print(end_price)
                
        # 计算指数移动平均（EMA）
        # EMA 给近期数据更大的权重
        N = 5
        weights = np.exp(np.linspace(-1, 0, N))
        weights /= weights.sum()
        print(weights)
        ema = np.convolve(weights,end_price)[N-1:-N+1]
        print(ema)
        
        t = np.arange(N-1,len(end_price))
        plt.plot(t,end_price[N-1:],lw=1.0)
        plt.plot(t,ema,lw=2.0)
        plt.show()


# 运行测试
if __name__ == '__main__':
    test = TestNumpyMA()
    # print("=== 测试 SMA ===")
    # test.testSMA()
    
    # print("\n=== 测试 EXP ===")
    # test.testEXP()
    
    print("\n=== 测试 EMA ===")
    test.testEMA()