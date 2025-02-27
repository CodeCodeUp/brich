from dealdata.get_data import get_data


def Solution_2(data):
    actual_bet_list = [0]
    total_integral = 1000
    actual_integral = 1000
    fib_sequence = [1, 1]  # Fibonacci sequence starts with the first element
    current_fib_index = 0  # Current index in the Fibonacci sequence
    current_streak = False  #
    actual_lose = 0  # 实际
    simulation_lose = 0  # 模拟

    for num_str in data:
        num = int(num_str)
        # 添加前期模拟数量过多清空策略
        # if (simulation_lose > 20) & (False == current_streak):
        #     current_streak = False
        #     simulation_lose = 0
        #     current_fib_index = 0
        #     actual_lose = 0
        if (simulation_lose < (-12)) & (False == current_streak):
            current_streak = True
            actual_lose = 0
            simulation_lose = 0
            current_fib_index = 0
        if actual_lose > 6:
            current_streak = False
            simulation_lose = 0
            current_fib_index = 0
            actual_lose = 0
        current_fib = fib_sequence[current_fib_index]
        bet = current_fib * 2
        if num < 5:  # Correct guess
            total_integral += bet * 0.8
            simulation_lose += bet * 0.8
            if current_streak:
                actual_lose += bet * 0.8
                actual_integral += bet * 0.8
                actual_bet_list.append(bet)
            current_fib_index -= 1  # 回退1
            if current_fib_index < 0:
                current_fib_index = 0
        else:  # Incorrect guess
            total_integral -= bet
            simulation_lose -= bet
            if current_streak:
                actual_lose -= bet
                actual_integral -= bet
                actual_bet_list.append(bet)
            # Move Fibonacci index forward by 1 and extend the sequence if needed
            current_fib_index += 1
            while current_fib_index >= len(fib_sequence):
                next_fib = fib_sequence[-1] + fib_sequence[-2]
                fib_sequence.append(next_fib)

    return [round(total_integral, 1), round(actual_integral, 1), round(simulation_lose, 1), round(actual_lose, 1), max(actual_bet_list)]


# 示例数据，包含数值
# 模拟减少积分大于n后，斐波那契归1后开始实际运行，实际积分大于m后。重新开始上述操作。
for col in ['number_one', 'number_two', 'number_three', 'number_four', 'number_five']:
    data = get_data()[col].tolist()
    final_integral = Solution_2(data)
    print(f"Solution_2-{col}最后的数量为: {final_integral}")


# 示例数据，包含数据

# choose
# 稳
# A [two:>=5,one:>=5]
# T [five:< 5,two:< 5,one:< 5]


def Solution_3(data):
    actual_bet_list = []
    total_integral = 1000
    actual_integral = 1000
    fib_sequence = [1, 1]  # Fibonacci sequence starts with the first element
    current_fib_index = 0  # Current index in the Fibonacci sequence
    current_streak = False  #
    actual_lose = 0  # 实际
    simulation_lose = 0  # 模拟
    actual_times = [False, 0, 0] # 是否标志，次数，实际获取数量

    for num_str in data:
        num = int(num_str)
        # Calculate current bet amount
        if (simulation_lose < (-12)) & (False == current_streak):
            current_streak = True
            actual_lose = 0
            simulation_lose = 0
            current_fib_index = 0
            actual_times = [True, 0, 0]
        if actual_lose > 5:
            current_streak = False
            simulation_lose = 0
            current_fib_index = 0
            actual_lose = 0
            actual_times = [False, 0, 0]
        if (actual_times[0] == True) & (actual_times[1] >= 10) & (actual_times[2] > 0):
            current_streak = False
            simulation_lose = 0
            current_fib_index = 0
            actual_lose = 0
            actual_times = [False, 0, 0]
        current_fib = fib_sequence[current_fib_index]
        bet = current_fib * 2
        if num >= 5:  # Correct guess
            total_integral += bet * 0.8
            simulation_lose += bet * 0.8
            if current_streak:
                actual_lose += bet * 0.8
                actual_integral += bet * 0.8
                actual_bet_list.append(bet)
                actual_times[1] = +1
                actual_times[2] = actual_integral - 1000
            current_fib_index -= 2  # 回退1
            if current_fib_index < 0:
                current_fib_index = 0
        else:  # Incorrect guess
            total_integral -= bet
            simulation_lose -= bet
            if current_streak:
                actual_lose -= bet
                actual_integral -= bet
                actual_bet_list.append(bet)
                actual_times[1] = +1
                actual_times[2] = actual_integral - 1000
            # Move Fibonacci index forward by 1 and extend the sequence if needed
            current_fib_index += 1
            while current_fib_index >= len(fib_sequence):
                next_fib = fib_sequence[-1] + fib_sequence[-2]
                fib_sequence.append(next_fib)

    return [round(total_integral, 1), round(actual_integral, 1), round(simulation_lose, 1), round(actual_lose, 1), max(actual_bet_list)]


# 示例数据，包含数值
# 模拟减少积分大于n后，斐波那契归1后开始实际运行，实际积分大于m后。重新开始上述操作。添加x次后依旧没有达到预期退出的策略。（效果差）
# data = get_data()['number_one'].tolist()
# final_integral = Solution_3(data)
# print(f"Solution_3最后的数量为: {final_integral}")

