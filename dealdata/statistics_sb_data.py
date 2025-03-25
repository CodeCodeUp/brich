
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
