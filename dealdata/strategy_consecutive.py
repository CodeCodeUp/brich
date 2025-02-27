import pandas as pd


def calculate_consecutive_big_small(df, columns, min_consecutive_count=5, max_consecutive_count=7):
    results = {}

    for col in columns:
        total_big_seqs = 0       # 总连续大≥5次的次数
        total_small_seqs = 0     # 总连续小≥5次的次数
        big_seqs_5_to_7 = 0      # 大连续5-7次
        small_seqs_5_to_7 = 0    # 小连续5-7次
        big_seqs_over_7 = 0      # 大连续>7次
        small_seqs_over_7 = 0    # 小连续>7次

        is_big = df[col] >= 5
        is_small = df[col] < 5

        count_big, count_small = 0, 0

        for i in range(len(df)):
            # 处理大
            if is_big[i]:
                count_big += 1
                if count_small >= min_consecutive_count:
                    total_small_seqs += 1

                    if count_small > max_consecutive_count:
                        # if col == 'number_one':
                        #     print(str(i) + '(>7)')
                        small_seqs_over_7 += 1
                    else:
                        # if col == 'number_one':
                        #     print(str(i) + '(' + str(count_small) + ')')
                        small_seqs_5_to_7 += 1
                count_small = 0
            else:
                if count_big >= min_consecutive_count:
                    total_big_seqs += 1

                    if count_big > max_consecutive_count:
                        big_seqs_over_7 += 1
                        # if col == 'number_one':
                        #     print(str(i) + '(>7)')
                    else:
                        big_seqs_5_to_7 += 1
                        # if col == 'number_one':
                        #     print(str(i) + '(' + str(count_big) + ')')
                count_big = 0

            # 处理小
            if is_small[i]:
                count_small += 1
                if count_big >= min_consecutive_count:
                    total_big_seqs += 1
                    if count_big > max_consecutive_count:
                        big_seqs_over_7 += 1
                    else:
                        big_seqs_5_to_7 += 1
                count_big = 0
            else:
                if count_small >= min_consecutive_count:
                    total_small_seqs += 1
                    if count_small > max_consecutive_count:
                        small_seqs_over_7 += 1
                    else:
                        small_seqs_5_to_7 += 1
                count_small = 0

        # 处理末尾未中断的序列
        for count, total, over, between in [
            (count_big, total_big_seqs, big_seqs_over_7, big_seqs_5_to_7),
            (count_small, total_small_seqs, small_seqs_over_7, small_seqs_5_to_7)
        ]:
            if count >= min_consecutive_count:
                total += 1
                if count > max_consecutive_count:
                    over += 1
                else:
                    between += 1

        results[col] = {
            '总连续大≥5次': big_seqs_5_to_7 + big_seqs_over_7,
            '总连续小≥5次': small_seqs_5_to_7 + small_seqs_over_7,
            '大连续5-7次': big_seqs_5_to_7,
            '小连续5-7次': small_seqs_5_to_7,
            '大连续>7次': big_seqs_over_7,
            '小连续>7次': small_seqs_over_7
        }

    return pd.DataFrame(results).T

