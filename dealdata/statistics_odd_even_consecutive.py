import pandas as pd


# 统计连续单/双超过5次的次数，连续单双超过5次且不超过7次的次数，连续单双7次的次数
def calculate_consecutive_odd_even(df, columns, min_consecutive_count=5, max_consecutive_count=6):
    results = {}

    for col in columns:
        total_odd_seqs = 0         # 总连续单数≥5次的次数
        total_even_seqs = 0        # 总连续双数≥5次的次数
        odd_seqs_5_to_7 = 0        # 单数连续5-7次
        even_seqs_5_to_7 = 0       # 双数连续5-7次
        odd_seqs_over_7 = 0        # 单数连续>7次
        even_seqs_over_7 = 0       # 双数连续>7次

        is_odd = df[col].apply(lambda x: 1 if int(x) % 2 != 0 else 0)  # 1表示单数，0表示双数
        is_even = df[col].apply(lambda x: 1 if int(x) % 2 == 0 else 0)

        count_odd, count_even = 0, 0

        for i in range(len(df)):
            # 处理单数
            if is_odd[i]:
                count_odd += 1
                if count_even >= min_consecutive_count:
                    total_even_seqs += 1
                    if count_even > max_consecutive_count:
                        even_seqs_over_7 += 1
                    else:
                        even_seqs_5_to_7 += 1
                count_even = 0
            else:
                if count_odd >= min_consecutive_count:
                    total_odd_seqs += 1
                    if count_odd > max_consecutive_count:
                        odd_seqs_over_7 += 1
                    else:
                        odd_seqs_5_to_7 += 1
                count_odd = 0

            # 处理双数
            if is_even[i]:
                count_even += 1
                if count_odd >= min_consecutive_count:
                    total_odd_seqs += 1
                    if count_odd > max_consecutive_count:
                        odd_seqs_over_7 += 1
                    else:
                        odd_seqs_5_to_7 += 1
                count_odd = 0
            else:
                if count_even >= min_consecutive_count:
                    total_even_seqs += 1
                    if count_even > max_consecutive_count:
                        even_seqs_over_7 += 1
                    else:
                        even_seqs_5_to_7 += 1
                count_even = 0

        # 处理末尾未中断的序列
        for count, total, over, between in [
            (count_odd, total_odd_seqs, odd_seqs_over_7, odd_seqs_5_to_7),
            (count_even, total_even_seqs, even_seqs_over_7, even_seqs_5_to_7)
        ]:
            if count >= min_consecutive_count:
                total += 1
                if count > max_consecutive_count:
                    over += 1
                else:
                    between += 1

        results[col] = {
            '总连续单数≥5次': odd_seqs_5_to_7 + odd_seqs_over_7,
            '总连续双数≥5次': even_seqs_5_to_7 + even_seqs_over_7,
            '单数连续5-7次': odd_seqs_5_to_7,
            '双数连续5-7次': even_seqs_5_to_7,
            '单数连续>7次': odd_seqs_over_7,
            '双数连续>7次': even_seqs_over_7
        }

    return pd.DataFrame(results).T
