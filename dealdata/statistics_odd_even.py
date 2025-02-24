import pandas as pd


def calculate_odd_even(df, columns):
    results = {}

    for col in columns:
        total_numbers = len(df[col])  # 统计总的数值数量

        # 统计单双数量
        odd_count = df[col].apply(lambda x: 1 if int(x) % 2 != 0 else 0).sum()  # 奇数数量
        even_count = total_numbers - odd_count  # 偶数数量，等于总数减去奇数数量

        # 计算单双概率
        odd_prob = odd_count / total_numbers  # 奇数概率
        even_prob = even_count / total_numbers  # 偶数概率

        # 将结果保存到字典中
        results[col] = {
            '奇数数量': odd_count,
            '偶数数量': even_count,
            '奇数概率': odd_prob,
            '偶数概率': even_prob
        }

    return pd.DataFrame(results).T



