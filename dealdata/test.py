import akshare as ak
import asyncio
import os
from datetime import datetime, timedelta

# 设置代理
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"

data_buffer = []


async def fetch_index_data():
    """异步获取上证指数数据"""
    while True:
        try:
            # 获取实时指数数据
            index_df = ak.stock_zh_index_spot_em()
            sh000001 = index_df[index_df["代码"] == "000001"]

            # 提取最新价并计算第二位小数
            current_price = sh000001['最新价'].values[0]
            second_decimal = int(round(current_price * 100, 2)) % 10

            # 记录当前时间和数字
            timestamp = datetime.now()
            data_buffer.append((timestamp, second_decimal))

            # 当缓存满30个数据点时处理
            if len(data_buffer) >= 30:
                process_data()
                data_buffer.clear()

        except Exception as e:
            print(f"数据获取失败: {e}")

        await asyncio.sleep(1)  # 精确的1秒间隔


def process_data():
    """处理30秒窗口数据"""
    if not data_buffer:
        return

    # 计算时间区间
    start_time = data_buffer[0][0]
    end_time = start_time + timedelta(seconds=30)

    # 格式化时间显示
    start_str = start_time.strftime("%H:%M:%S.%f")[:-4]
    end_str = end_time.strftime("%H:%M:%S.%f")[:-4]

    # 统计大小比例
    big_count = sum(1 for item in data_buffer if item[1] >= 5)
    small_count = 30 - big_count

    # 输出结果
    print(f"{start_str}-{end_str} 大：{big_count / 30:.0%} 小：{small_count / 30:.0%}")


async def main():
    """主异步任务"""
    await fetch_index_data()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("程序已终止")