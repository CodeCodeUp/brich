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


def is_D(num):
    if num == -1:
        return False
    else:
        if num % 2 == 0:
            return True
        else:
            return False


def is_O(num):
    if num == -1:
        return False
    else:
        if num % 2 != 0:
            return True
        else:
            return False


def Solution_times_B(base_data):
    actual_bet_list = [0]
    total_integral = 2000      # 初始总积分
    # fib_sequence = [1, 1, 2, 3, 5, 8, 13]       # 斐波那契数列初始化
    # fib_sequence_first = [8, 13, 13, 21, 21, 34, 34, 55, 55, 89, 89, 144, 144, 233, 233]       # 斐波那契数列初始化
    fib_sequence = [1, 1, 2, 3, 5, 8, 8, 13]       # 斐波那契数列初始化
    current_streak = 0           # 连续「大」的次数
    in_betting_group = False     # 是否在下注组中
    initial_bet = 5             #
    profit_target = 0           #
    current_fib_index = 0        # 当前斐波那契索引（每次触发下注组时重置）
    trigger_integral = 0        # 触发下注组时的初始积分
    begin = 9
    rollback = 1

    for num_str in base_data:
        num = int(num_str)
        if current_streak >= begin:
            current_streak = current_streak + 1 if not is_S(num) else 0
        else:
            current_streak = current_streak + 1 if is_B(num) else 0
        if not in_betting_group:

            if current_streak >= begin:
                in_betting_group = True
                current_fib_index = 0
                profit_target = initial_bet * 3
                trigger_integral = total_integral  # 记录触发时的积分
        else:
            # 动态扩展斐波那契数列（确保索引有效）
            while current_fib_index >= len(fib_sequence):
                if fib_sequence[-1] != fib_sequence[-2]:
                    fib_sequence.append(fib_sequence[-1])
                else:
                    fib_sequence.append(fib_sequence[-1] + fib_sequence[-3])

            # 计算本次下注金额（基于斐波那契索引）
            bet = initial_bet * fib_sequence[current_fib_index]
            actual_bet_list.append(bet)
            if total_integral < bet:
                break  # 积分不足，终止策略

            # 扣除积分并更新当前下注组的总下注金额
            total_integral -= bet

            if is_S(num):
                total_integral += bet * 2
                if total_integral >= trigger_integral + profit_target:
                    in_betting_group = False  # 达标后退出下注组
                    current_fib_index = 0     # 重置索引
                else:
                    if current_fib_index <= 5:
                        current_fib_index = max(0, current_fib_index - 2)
                    else:
                        current_fib_index = max(0, current_fib_index - rollback)  # 保守回退2级
                        if rollback == 2:
                            rollback = 1
                        else:
                            rollback = 2
            else:  # 猜「小」失败
                current_fib_index += 1

    return [round(total_integral, 1), max(actual_bet_list), fib_sequence,current_fib_index]


for col in ['number_four']:
    data = get_data()[col].tolist()
    final_integral_times_B = Solution_times_B(data)
    print(f"Solution_times_B-{col}最后的数量为: {final_integral_times_B}")
