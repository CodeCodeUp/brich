import pandas as pd


def calculate_big_small_statistics(df, columns):
    results = {}

    # 对每一列（位置）进行处理
    for col in columns:
        # 定义“大”和“小”的条件
        is_big = df[col] >= 5  # 大于等于5是“大”
        is_small = df[col] < 5  # 小于5是“小”

        # 计算大和小的次数
        big_count = is_big.sum()  # 大的数量
        small_count = is_small.sum()  # 小的数量

        # 计算大和小的概率
        total_count = len(df)  # 总行数
        big_prob = big_count / total_count
        small_prob = small_count / total_count

        # 存储结果
        results[col] = {
            'big_count': big_count,
            'small_count': small_count,
            'big_prob': big_prob,
            'small_prob': small_prob
        }

    return pd.DataFrame(results).T  # 转置为列格式
