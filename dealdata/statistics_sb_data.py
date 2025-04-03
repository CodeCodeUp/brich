from collections import Counter


def get_result(data):
    # 将每个数字转换为对应的标签
    labels = []
    for num in data:
        num = int(num)
        if num == -1:
            labels.append('m')
        elif 4 <= num <= 10:
            labels.append('s')
        elif 11 <= num <= 17:
            labels.append('D')


    result = []
    if labels:
        current_label = labels[0]
        current_str = current_label
        for label in labels[1:]:
            if label == current_label:
                current_str += label
            else:
                result.append(current_str)
                current_label = label
                current_str = label
        result.append(current_str)  # 添加最后一个段

    return result


def get_ds_result(data):
    # 将每个数字转换为对应的标签
    labels = []
    for num in data:
        num = int(num)
        if num == -1:
            labels.append('m')
        elif num % 2 != 0:
            labels.append('o')
        elif num % 2 == 0:
            labels.append('S')

    # 统计连续出现的长龙情况
    result = []
    if labels:
        current_label = labels[0]
        current_str = current_label
        for label in labels[1:]:
            if label == current_label:
                current_str += label
            else:
                result.append(current_str)
                current_label = label
                current_str = label
        result.append(current_str)  # 添加最后一个段

    return result


def count_sb_odds_evens(data):
    def is_odd(num):
        num = int(num)
        return 4 <= num <= 10

    odd_counts = []
    even_counts = []

    # 初始化计数
    current_count = 1
    is_current_odd = is_odd(data[0])

    # 遍历数据并统计连续单数或双数
    for i in range(1, len(data)):
        if int(data[i]) == -1:
            # 遇到-1，重置计数
            if is_current_odd:
                odd_counts.append(current_count)
            else:
                even_counts.append(current_count)
            is_current_odd = is_odd(data[i])
            current_count = 1
            continue
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

    return odd_count_results, even_count_results