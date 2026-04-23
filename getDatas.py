import baostock as bs
import pandas as pd
from datetime import datetime, timedelta
import time
import os

def get_single_stock_data(stock_code, start_date, end_date, chunk_months=6, max_retries=3, request_interval=3):
    """
    获取单只股票数据（内部函数）
    """
    all_dataframes = []
    current_start = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    
    segment_count = 0
    failed_segments = []
    last_request_time = 0
    
    while current_start < end_dt:
        current_end = min(current_start + timedelta(days=chunk_months * 30), end_dt)
        
        segment_start_str = current_start.strftime("%Y-%m-%d")
        segment_end_str = current_end.strftime("%Y-%m-%d")
        
        segment_count += 1
        
        # 确保请求间隔
        current_time = time.time()
        time_since_last_request = current_time - last_request_time
        if last_request_time > 0 and time_since_last_request < request_interval:
            wait_time = request_interval - time_since_last_request
            time.sleep(wait_time)
        
        last_request_time = time.time()
        
        success = False
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    wait_time = request_interval * attempt
                    time.sleep(wait_time)
                    bs.logout()
                    time.sleep(1)
                    bs.login()
                
                rs = bs.query_history_k_data_plus(
                    stock_code,
                    "date,code,open,high,low,close,volume,amount,adjustflag",
                    start_date=segment_start_str,
                    end_date=segment_end_str,
                    frequency="d",
                    adjustflag="3"
                )
                
                if rs.error_code != '0':
                    if attempt < max_retries - 1:
                        continue
                    failed_segments.append((segment_start_str, segment_end_str))
                    break
                
                data_list = []
                while (rs.error_code == '0') & rs.next():
                    data_list.append(rs.get_row_data())
                
                if data_list:
                    df_segment = pd.DataFrame(data_list, columns=rs.fields)
                    all_dataframes.append(df_segment)
                    success = True
                    break
                else:
                    success = True
                    break
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    continue
                failed_segments.append((segment_start_str, segment_end_str))
        
        if not success:
            print(f"    ✗ 达到最大重试次数，跳过该段")
        
        current_start = current_end + timedelta(days=1)
    
    if not all_dataframes:
        return None, failed_segments
    
    df = pd.concat(all_dataframes, ignore_index=True)
    df.drop_duplicates(subset=['date'], keep='first', inplace=True)
    
    df.rename(columns={
        "code": "stock_id",
        "date": "date",
        "close": "close",
        "open": "open",
        "high": "high",
        "low": "low",
        "volume": "volume"
    }, inplace=True)
    
    cols = ['stock_id', 'date', 'close', 'open', 'high', 'low', 'volume']
    missing_cols = [col for col in cols if col not in df.columns]
    if missing_cols:
        return None, failed_segments
    
    df = df[cols]
    df.sort_values(by='date', inplace=True)
    
    return df, failed_segments


def get_stock_data_baostock(stock_codes, start_date="2023-01-01", end_date="2023-12-31", 
                           chunk_months=6, max_retries=3, request_interval=3, 
                           output_dir="./stock_data", save_mode="separate"):
    """
    批量获取多只股票数据并保存为 CSV
    
    参数:
        stock_codes: 股票代码列表，如 ["sh.600519", "sz.000001", "sh.600036"]
                     也可以是单个字符串 "sh.600519"
        start_date: 开始日期，格式 YYYY-MM-DD
        end_date: 结束日期，格式 YYYY-MM-DD
        chunk_months: 每段月数，默认6个月
        max_retries: 最大重试次数，默认3次
        request_interval: 请求间隔秒数，默认3秒
        output_dir: 输出目录，默认 ./stock_data
        save_mode: 保存模式
                  - "separate": 每只股票单独保存为一个文件（默认）
                  - "merged": 所有股票合并为一个文件
    """
    # 如果传入的是单个字符串，转换为列表
    if isinstance(stock_codes, str):
        stock_codes = [stock_codes]
    
    if not stock_codes:
        print("❌ 股票代码列表为空")
        return
    
    # 创建输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"✅ 创建输出目录: {output_dir}")
    
    # 登录系统
    lg = bs.login()
    if lg.error_code != '0':
        print(f"登录失败: {lg.error_msg}")
        return
    
    print(f"📊 批量获取股票数据")
    print(f"股票数量: {len(stock_codes)}")
    print(f"时间范围: {start_date} 至 {end_date}")
    print(f"分段策略: 每 {chunk_months} 个月一段")
    print(f"重试策略: 最多 {max_retries} 次")
    print(f"请求间隔: {request_interval} 秒")
    print(f"保存模式: {save_mode}")
    print(f"输出目录: {output_dir}\n")
    
    all_stocks_data = {}
    failed_stocks = []
    total_segments_success = 0
    total_segments_failed = 0
    
    # 遍历每只股票
    for idx, stock_code in enumerate(stock_codes, 1):
        print(f"\n{'='*60}")
        print(f"[{idx}/{len(stock_codes)}] 处理股票: {stock_code}")
        print(f"{'='*60}")
        
        try:
            df, failed_segments = get_single_stock_data(
                stock_code, start_date, end_date, 
                chunk_months, max_retries, request_interval
            )
            
            if df is not None and not df.empty:
                all_stocks_data[stock_code] = df
                total_segments_success += len(df) // (chunk_months * 20)  # 估算成功段数
                print(f"✅ {stock_code} 获取成功: {len(df)} 条记录")
                
                # 如果是单独保存模式，立即保存
                if save_mode == "separate":
                    file_name = f"{stock_code.replace('.', '_')}.csv"
                    file_path = os.path.join(output_dir, file_name)
                    df.to_csv(file_path, index=False, encoding='gbk')
                    print(f"💾 已保存至: {file_path}")
            else:
                failed_stocks.append(stock_code)
                print(f"❌ {stock_code} 获取失败")
            
            if failed_segments:
                total_segments_failed += len(failed_segments)
                print(f"⚠️  {len(failed_segments)} 个时间段获取失败")
            
            # 每只股票之间增加额外间隔，避免过于频繁
            if idx < len(stock_codes):
                print(f"⏳ 等待 {request_interval * 2} 秒后处理下一只股票...")
                time.sleep(request_interval * 2)
                
        except Exception as e:
            print(f"❌ {stock_code} 处理异常: {str(e)[:100]}")
            failed_stocks.append(stock_code)
    
    # 如果是合并保存模式，合并所有数据
    if save_mode == "merged" and all_stocks_data:
        print(f"\n{'='*60}")
        print("合并所有股票数据...")
        print(f"{'='*60}")
        
        merged_df = pd.concat(all_stocks_data.values(), ignore_index=True)
        merged_df.sort_values(by=['stock_id', 'date'], inplace=True)
        
        file_name = f"merged_stocks_{start_date}_to_{end_date}.csv"
        file_path = os.path.join(output_dir, file_name)
        merged_df.to_csv(file_path, index=False, encoding='gbk')
        print(f"✅ 合并数据已保存至: {file_path}")
        print(f"   总记录数: {len(merged_df)}")
        print(f"   股票数量: {len(all_stocks_data)}")
    
    # 退出系统
    bs.logout()
    
    # 打印总结
    print(f"\n{'='*60}")
    print("📋 批量获取完成总结")
    print(f"{'='*60}")
    print(f"✅ 成功: {len(all_stocks_data)} 只股票")
    print(f"❌ 失败: {len(failed_stocks)} 只股票")
    if failed_stocks:
        print(f"   失败列表: {', '.join(failed_stocks)}")
    print(f"📊 总数据量: {total_segments_success} 条记录")
    if total_segments_failed > 0:
        print(f"⚠️  失败段数: {total_segments_failed}")
    print(f"{'='*60}")


if __name__ == '__main__':
    # ========== 使用示例 ==========
    
    # 示例1: 获取单只股票
    # get_stock_data_baostock("sh.600519", "2024-01-01", "2026-04-23")
    
    # 示例2: 批量获取多只股票（单独保存）
    stock_list = [
        "sh.600519",  # 贵州茅台
        "sz.000001",  # 平安银行
        "sh.600036",  # 招商银行
        "sz.000858",  # 五粮液
        "sh.601318",  # 中国平安
    ]
    
    get_stock_data_baostock(
        stock_codes=stock_list,
        start_date="2026-01-01",
        end_date="2026-04-23",
        chunk_months=6,
        max_retries=3,
        request_interval=3,
        output_dir="./stock_data",
        save_mode="separate"  # 每只股票单独保存
    )
    
    # 示例3: 批量获取并合并为一个文件
    # get_stock_data_baostock(
    #     stock_codes=stock_list,
    #     start_date="2024-01-01",
    #     end_date="2026-04-23",
    #     chunk_months=6,
    #     max_retries=3,
    #     request_interval=3,
    #     output_dir="./stock_data",
    #     save_mode="merged"  # 合并为一个文件
    # )
