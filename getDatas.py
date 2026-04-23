import baostock as bs
import pandas as pd

def get_stock_data_baostock(stock_code="sh.600519", start_date="2023-01-01", end_date="2023-12-31"):
    """
    使用 Baostock 获取 A 股数据并保存为 CSV
    """
    # 1. 登录系统
    lg = bs.login()
    if lg.error_code != '0':
        print(f"登录失败: {lg.error_msg}")
        return

    print(f"正在获取 {stock_code} 的数据...")

    # 2. 获取历史 K 线数据
    # fields 参数定义了我们要哪些列
    rs = bs.query_history_k_data_plus(
        stock_code,
        "date,code,open,high,low,close,volume,amount,adjustflag",
        start_date=start_date,
        end_date=end_date,
        frequency="d",       # d=日k线
        adjustflag="3"       # 3=后复权 (也可以选 2=前复权)
    )

    # 3. 转换结果为 DataFrame
    data_list = []
    while (rs.error_code == '0') & rs.next():
        data_list.append(rs.get_row_data())
    
    df = pd.DataFrame(data_list, columns=rs.fields)

    # 4. 数据清洗与重命名 (匹配你之前的格式)
    df.rename(columns={
        "code": "stock_id",
        "date": "date",
        "close": "close",
        "open": "open",
        "high": "high",
        "low": "low",
        "volume": "volume"
    }, inplace=True)

    # 选取需要的列
    cols = ['stock_id', 'date', 'close', 'open', 'high', 'low', 'volume']
    df = df[cols]

    # 5. 保存为 CSV
    file_name = f"{stock_code.replace('.', '_')}.csv"
    df.to_csv(file_name, index=False, encoding='gbk')
    print(f"✅ 数据已成功保存至: {file_name}")

    # 6. 退出系统
    bs.logout()

if __name__ == '__main__':
    # 注意：Baostock 的 A 股代码格式是 sh.600519 或 sz.000001
    get_stock_data_baostock("sh.600519", "2023-01-01", "2023-12-31")
