import akshare as ak
import asyncio
import os
from datetime import datetime, timedelta
from collections import defaultdict

os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"

# 存储时间窗口数据的字典 {窗口开始时间: [去重后的数字列表]}
window_data = defaultdict(list)
last_digit = None  # 用于去重的临时变量


def get_window_info(timestamp):
    """获取时间戳对应的30秒窗口信息"""
    aligned = timestamp.replace(second=timestamp.second // 30 * 30, microsecond=0)
    window_start = aligned
    window_end = window_start + timedelta(seconds=30)
    return window_start, window_end


async def fetch_index_data():
    """异步获取指数数据（包含执行时间补偿）"""
    global last_digit
    while True:
        start_time = datetime.now()
        try:
            # 获取实时数据
            index_df = ak.stock_zh_index_spot_em()
            sh000001 = index_df[index_df["代码"] == "000001"]

            # 提取第二位小数
            current_price = sh000001['最新价'].values[0]
            current_digit = int(round(current_price * 100, 2)) % 10

            # 获取当前时间戳
            now = datetime.now()

            # 确定所属时间窗口
            window_start, window_end = get_window_info(now)

            # 去重处理（跨窗口重置last_digit）
            if not window_data[window_start] or current_digit != last_digit:
                window_data[window_start].append(current_digit)
                last_digit = current_digit

        except Exception as e:
            print(f"数据获取失败: {e}")

        # 动态补偿时间间隔
        elapsed = (datetime.now() - start_time).total_seconds()
        await asyncio.sleep(max(0, 1 - elapsed))


async def monitor_windows():
    """监控时间窗口并输出结果"""
    while True:
        now = datetime.now()

        # 检查所有未处理的窗口
        for window_start in list(window_data.keys()):
            window_end = window_start + timedelta(seconds=30)

            # 如果当前时间超过窗口结束时间
            if now >= window_end:
                digits = window_data.pop(window_start)

                # 统计大小比例
                big = sum(1 for d in digits if d >= 5)
                total = len(digits)
                ratio_big = big / total if total else 0
                ratio_small = 1 - ratio_big

                # 格式化时间输出
                start_str = window_start.strftime("%H:%M:%S") + ".00"
                end_str = window_end.strftime("%H:%M:%S") + ".00"

                print(f"{start_str}-{end_str} 大：{ratio_big:.0%} 小：{ratio_small:.0%}")

        await asyncio.sleep(0.1)  # 每100ms检查一次


async def main():
    """主异步任务"""
    await asyncio.gather(
        fetch_index_data(),
        monitor_windows()
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("程序已终止")