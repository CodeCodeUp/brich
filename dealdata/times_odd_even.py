# 统计单/双 连续出现n次的次数
from collections import Counter


def count_consecutive_odds_evens(data):
    # 判断数字是单数（奇数）还是双数（偶数）
    def is_odd(num):
        return num % 2 != 0

    # 存储连续单数和双数的出现次数
    odd_counts = []
    even_counts = []

    # 初始化计数
    current_count = 1
    is_current_odd = is_odd(data[0])

    # 遍历数据并统计连续单数或双数
    for i in range(1, len(data)):
        if is_odd(data[i]) == is_current_odd:
            current_count += 1
        else:
            if is_current_odd:
                odd_counts.append(current_count)
            else:
                even_counts.append(current_count)
            is_current_odd = is_odd(data[i])
            current_count = 1

    # 不要忘了添加最后一组连续计数
    if is_current_odd:
        odd_counts.append(current_count)
    else:
        even_counts.append(current_count)

    # 使用Counter统计每个连续次数出现的次数
    odd_count_results = Counter(odd_counts)
    even_count_results = Counter(even_counts)

    # 输出统计结果
    print("统计结果：")

    # 打印单数（奇数）的统计结果
    print("\n单数（奇数）连续出现次数：")
    if odd_count_results:
        for count, freq in sorted(odd_count_results.items()):
            print(f"连续 {count} 次: {freq} 次")
    else:
        print("没有连续的单数出现！")

    # 打印双数（偶数）的统计结果
    print("\n双数（偶数）连续出现次数：")
    if even_count_results:
        for count, freq in sorted(even_count_results.items()):
            print(f"连续 {count} 次: {freq} 次")
    else:
        print("没有连续的双数出现！")


