from dealdata.get_data import get_data


def Solution_1(data):
    counts = [0] * 10  # 初始化计数器，所有数字未出现次数为0

    for v in data:
        for d in range(10):
            if d != v:
                counts[d] += 1  # 非当前数字的计数器加1
            else:
                counts[d] = 0   # 当前数字的计数器重置为0
        # 格式化输出
        output = f"{v}: ["
        for i in range(10):
            output += f"{i}({counts[i]})"
            if i != 9:
                output += ", "
        output += "]"
        print(output)


Solution_1(get_data()['number_one'].tolist())
