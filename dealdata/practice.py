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


def Solution_2(data):
    total_integral = 1000
    actual_integral = 1000
    fib_sequence = [1, 1]  # Fibonacci sequence starts with the first element
    current_fib_index = 0  # Current index in the Fibonacci sequence
    current_streak = False  #
    actual_lose = 0  # 实际
    simulation_lose = 0  # 模拟

    for num_str in data:
        num = int(num_str)
        # Calculate current bet amount
        if (simulation_lose < (-12)) & (current_streak == False):
            current_streak = True
            actual_lose = 0
            simulation_lose = 0
            current_fib_index = 0
        if actual_lose > 5:
            current_streak = False
            simulation_lose = 0
            current_fib_index = 0
            actual_lose = 0
        current_fib = fib_sequence[current_fib_index]
        bet = current_fib * 2
        if num >= 5:  # Correct guess
            total_integral += bet * 0.8
            simulation_lose += bet * 0.8
            if current_streak:
                actual_lose += bet * 0.8
                actual_integral += bet * 0.8
                print(actual_integral)
            current_fib_index -= 1  # 回退1
            if current_fib_index < 0:
                current_fib_index = 0
        else:  # Incorrect guess
            total_integral -= bet
            simulation_lose -= bet
            if current_streak:
                actual_lose -= bet
                actual_integral -= bet
                print(actual_integral)
            # Move Fibonacci index forward by 1 and extend the sequence if needed
            current_fib_index += 1
            while current_fib_index >= len(fib_sequence):
                next_fib = fib_sequence[-1] + fib_sequence[-2]
                fib_sequence.append(next_fib)

    return [round(total_integral, 1), round(actual_integral, 1), round(simulation_lose, 1), round(actual_lose, 1), fib_sequence]


# 示例数据，包含数值
data = get_data()['number_one'].tolist()
final_integral = Solution_1(data)
print(f"Solution_1最后的数量为: {final_integral}")

# 示例数据，包含数值
# 模拟减少积分大于20后，斐波那契归1后开始实际运行，实际积分大于10后。重新开始上述操作。
data = get_data()['number_one'].tolist()
final_integral = Solution_2(data)
print(f"Solution_2最后的数量为: {final_integral}")

# 示例数据，包含数据

# choose
# 稳
# A [two:>=5,one:>=5]
# T [five:< 5,two:< 5,one:< 5]


