from get_data import get_data

data = get_data()['number_four'].tolist()  # 示例输入，可以替换成实际数据


# 将每个数字转换为对应的标签
labels = []
for num in data:
    num = int(num)
    if num == -1:
        labels.append('mid')
    elif 4 <= num <= 10:
        labels.append('小')
    elif 11 <= num <= 17:
        labels.append('大')

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

# 输出结果，每个长龙占一行
for s in result:
    print(s)