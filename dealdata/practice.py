from dealdata.get_data import get_data


def Solution_1(data):
    total_integral = 1000
    fib_sequence = [1, 1]  # 斐波那契数列初始化
    current_fib_index = 0  # 当前斐波那契索引
    current_streak = 0  # 连续「大」的次数
    in_betting_group = False
    remaining_bets = 0

    for num_str in data:
        num = int(num_str)
        if not in_betting_group:
            # 统计连续「大」的次数
            if num >= 5:
                current_streak += 1
            else:
                current_streak = 0

            # 触发下注条件：连续5次大
            if current_streak >= 5:
                in_betting_group = True
                remaining_bets = 3
                current_streak = 0  # 重置计数器
        else:
            if remaining_bets > 0:
                # 动态扩展斐波那契数列（确保索引有效）
                while current_fib_index >= len(fib_sequence):
                    fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])

                # 计算本次下注数量
                bet = 2 * fib_sequence[current_fib_index]
                # print(str(bet))
                if total_integral < bet:
                    break  # 数量不足，终止策略

                total_integral -= bet  # 扣除数量
                if num < 5:  # 猜「小」成功
                    total_integral += bet * 1.8
                    current_fib_index = max(0, current_fib_index - 2)
                    in_betting_group = False  # 提前退出组
                    remaining_bets = 0
                else:  # 猜「小」失败
                    current_fib_index += 1
                    remaining_bets -= 1
                    if remaining_bets == 0:
                        in_betting_group = False  # 完成3次下注后退出组

    return round(total_integral, 1)


for col in ['number_one', 'number_two', 'number_three', 'number_four', 'number_five']:
    data = get_data()[col].tolist()
    final_integral = Solution_1(data)
    print(f"Solution_2-{col}最后的数量为: {final_integral}")




