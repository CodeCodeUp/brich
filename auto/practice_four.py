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


def is_E(num):
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


def Solution_times(base_data):
    actual_bet_list = [0]
    fib_sequence = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377]
    current_fib_index = 0
    begin_bet = 10
    total_integral = 1000
    current_streak = 0
    in_betting_group = False
    initial_bet = begin_bet
    begin = 7

    for num_str in base_data:
        num = int(num_str)

        if not in_betting_group:
            current_streak = current_streak + 1 if is_B(num) else 0
            if current_streak >= begin:
                in_betting_group = True
        else:
            current_streak = current_streak + 1 if not is_S(num) else 0
            # 扣除积分并更新当前下注组的总下注金额
            initial_bet = begin_bet * fib_sequence[current_fib_index]
            total_integral -= initial_bet
            actual_bet_list.append(initial_bet)
            if is_S(num):
                total_integral += initial_bet * 2
                in_betting_group = False
                current_streak = 0
                current_fib_index = max(0, current_fib_index - 2)
                continue
            else:
                current_fib_index += 1
        if current_streak >= 8:
            current_streak = 0
            in_betting_group = False
            continue
    return [round(total_integral, 1), max(actual_bet_list), fib_sequence]


def Solution_times_double(base_data):
    begin_bet = 50
    total_integral = 1000
    current_streak = 0
    in_betting_group = False
    initial_bet = begin_bet
    begin = 10
    max_bet = begin_bet

    for num_str in base_data:
        num = int(num_str)

        if not in_betting_group:
            current_streak = current_streak + 1 if is_B(num) else 0
            if current_streak >= begin:
                in_betting_group = True
        else:
            current_streak = current_streak + 1 if not is_S(num) else 0
            total_integral -= initial_bet
            if is_S(num):
                total_integral += initial_bet * 2
                initial_bet = begin_bet
                in_betting_group = False
                current_streak = 0
                continue
            else:
                initial_bet *= 2
            max_bet = max(max_bet, initial_bet)
        if current_streak >= begin + 1:
            current_streak = 0
            in_betting_group = False
            continue
    return [round(total_integral, 1), max_bet]


for col in ['number_four']:
    data = get_data()[col].tolist()
    final_integral_times_B = Solution_times(data)
    Solution_times_double_B = Solution_times_double(data)
    print(f"Solution_times_B-{col}最后的数量为: {final_integral_times_B}")
    print(f"Solution_times_double_B-{col}最后的数量为: {Solution_times_double_B}")

