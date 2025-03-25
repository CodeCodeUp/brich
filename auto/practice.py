from get_data import get_data


def is_B(num):
    if 11 <= num <= 17:
        return True
    else:
        return False


def is_S(num):
    if 4 <= num <= 10:
        return True
    else:
        return False


def Solution(base_data):
    actual_bet_list = [0]
    total_integral = 1000
    actual_integral = 1000
    fib_sequence = [1, 1]  # Fibonacci sequence starts with the first element
    current_fib_index = 0  # Current index in the Fibonacci sequence
    current_streak = False  #
    actual_lose = 0  # 实际
    simulation_lose = 0  # 模拟

    for num_str in base_data:
        num = int(num_str)
        # 添加前期模拟数量过多清空策略
        if (simulation_lose > 20) and (current_streak == False):
            current_streak = False
            simulation_lose = 0
            current_fib_index = 0
            actual_lose = 0
        if (simulation_lose < (-35)) and (False == current_streak):
            current_streak = True
            actual_lose = 0
            simulation_lose = 0
            current_fib_index = 0
        if actual_lose > 15:
            current_streak = False
            simulation_lose = 0
            # current_fib_index = -2
            current_fib_index = 0
            actual_lose = 0
        current_fib = fib_sequence[current_fib_index]
        bet = current_fib * 5
        if is_B(num):  # Correct guess
            total_integral += bet * 1
            simulation_lose += bet * 1
            if current_streak:
                actual_lose += bet * 1
                actual_integral += bet * 1
                actual_bet_list.append(bet)
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
                if actual_integral < 0:
                    print(f"{col}出现小于0: {actual_integral}")
            # Move Fibonacci index forward by 1 and extend the sequence if needed
            current_fib_index += 1
            while current_fib_index >= len(fib_sequence):
                next_fib = fib_sequence[-1] + fib_sequence[-2]
                fib_sequence.append(next_fib)

    return [round(total_integral, 1), round(actual_integral, 1), round(simulation_lose, 1), round(actual_lose, 1),
            max(actual_bet_list)]


def Solution_times(base_data):
    actual_bet_list = [0]
    total_integral = 1000      # 初始总积分
    fib_sequence = [1, 1]       # 斐波那契数列初始化
    current_streak = 0           # 连续「大」的次数
    in_betting_group = False     # 是否在下注组中
    initial_bet = 4             # 初始固定为2
    profit_target = 0           #
    current_fib_index = 0        # 当前斐波那契索引（每次触发下注组时重置）
    trigger_integral = 0        # 触发下注组时的初始积分

    for num_str in base_data:
        num = int(num_str)
        if not in_betting_group:
            # 统计连续「大」的次数
            current_streak = current_streak + 1 if is_B(num) else 0

            # 触发下注条件：连续5次大
            if current_streak >= 5:
                in_betting_group = True
                current_streak = 0
                current_fib_index = 0          # 重置斐波那契索引（确保首次下注为2）
                profit_target = initial_bet * 3  # 固定盈利目标为6
                trigger_integral = total_integral  # 记录触发时的积分
        else:
            # 动态扩展斐波那契数列（确保索引有效）
            while current_fib_index >= len(fib_sequence):
                fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])

            # 计算本次下注金额（基于斐波那契索引）
            bet = 2 * fib_sequence[current_fib_index]
            actual_bet_list.append(bet)
            if total_integral < bet:
                break  # 积分不足，终止策略

            # 扣除积分并更新当前下注组的总下注金额
            total_integral -= bet

            if not is_B(num) and num != -1: # 猜「小」成功
                total_integral += bet * 2
                if total_integral >= trigger_integral + profit_target:
                    in_betting_group = False  # 达标后退出下注组
                    current_fib_index = 0     # 重置索引
                else:
                    current_fib_index = max(0, current_fib_index - 2)  # 保守回退2级
            else:  # 猜「小」失败
                current_fib_index += 1

    return [round(total_integral, 1), max(actual_bet_list)]


for col in ['number_four']:
    data = get_data()[col].tolist()
    final_integral = Solution(data)
    final_integral_times = Solution_times(data)
    print(f"Solution-{col}最后的数量为: {final_integral}")
    print(f"Solution_times-{col}最后的数量为: {final_integral_times}")