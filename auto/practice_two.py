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


def Solution_times_B(base_data):
    begin_bet = 10
    total_integral = 1000      # 初始总积分
    current_streak = 0           # 连续「大」的次数
    in_betting_group = False     # 是否在下注组中
    initial_bet = begin_bet             #
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
            total_integral -= initial_bet

            if is_S(num):
                total_integral += initial_bet * 2
                in_betting_group = False
                current_streak = 0
                initial_bet = begin_bet
                continue
            else:
                initial_bet *= 2
        if current_streak >= 10:
            current_streak = 0
            initial_bet = begin_bet
            in_betting_group = False
            continue
    return [round(total_integral, 1)]


for col in ['number_four']:
    data = get_data()[col].tolist()
    final_integral_times_B = Solution_times_B(data)
    print(f"Solution_times_B-{col}最后的数量为: {final_integral_times_B}")

