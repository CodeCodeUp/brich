from dealdata.probability_calculator import ProbabilityCalculator
from get_data import get_data
from strategy_big_small import calculate_big_small_statistics
from strategy_consecutive import calculate_consecutive_big_small
from statistics_odd_even import calculate_odd_even
from statistics_odd_even_consecutive import calculate_consecutive_odd_even
from statistics_big_small_continue import analyze_data
from times_odd_even import count_consecutive_odds_evens


def main():
    # 获取数据
    df = get_data()

    # 计算“大”和“小”的规律
    statistics = calculate_big_small_statistics(df, ['number_one', 'number_two', 'number_three', 'number_four',
                                                     'number_five'])
    # 计算连续出现4次“大”或“小”的次数，并且它们之间的间隔不超过7的次数
    consecutive_stats = calculate_consecutive_big_small(df, ['number_one', 'number_two', 'number_three', 'number_four',
                                                             'number_five'])
    # 计算“单”和“双”的规律
    calculate_data = calculate_odd_even(df,['number_one', 'number_two', 'number_three', 'number_four', 'number_five'])
    # 统计连续单/双超过4次的次数，连续单双超过4次且不超过7次的次数，连续单双7次的次数
    calculate_consecutive_data = calculate_consecutive_odd_even(df,['number_one', 'number_two', 'number_three',
                                                                    'number_four', 'number_five'])


    # 打印结果
    print('大小概率')
    print(statistics)

    # 连续出现4次大或者连续出现4次小的次数，并且其中连续出现4次大或者连续出现4次小不联系超过7次 的次数
    print()
    print('连续出现4次大或者连续出现4次小的次数，并且其中连续出现4次大或者连续出现4次小不联系超过7次 的次数')
    print()
    print(consecutive_stats)

    print()
    print('单双概率')
    print()
    print(calculate_data)

    # 统计连续单/双超过4次的次数，连续单双超过4次且不超过7次的次数，连续单双7次的次数
    print()
    print('统计连续单/双超过4次的次数，连续单双超过4次且不超过7次的次数，连续单双7次的次数')
    print()
    print(calculate_consecutive_data)

    # 统计连续单/双超过4次的次数，连续单双超过4次且不超过7次的次数，连续单双7次的次数
    print()
    print('# 统计每个数字的概率')
    # 创建概率计算器对象
    probability_calculator = ProbabilityCalculator(df, ['number_one', 'number_two', 'number_three', 'number_four', 'number_five'])
    # 计算概率并打印结果
    result = probability_calculator.print_probability()
    print("每列数字出现次数：")
    print(result[0])
    print("\n每列数字出现概率：")
    print(result[1])

    print()

    print('# 统计大小总的连续情况')
    for col in ['number_one', 'number_two', 'number_three', 'number_four', 'number_five']:
        data = analyze_data(df[col].tolist())
        print(f"{col}:{data}")

    print('统计 大/小 连续出现n次的次数')
    for col in ['number_one', 'number_two', 'number_three', 'number_four', 'number_five']:
        result = count_consecutive_odds_evens(df[col].tolist())
        # 打印单数（奇数）的统计结果
        print(f"{col}小数连续出现次数：")
        if result[0]:
            for count, freq in sorted(result[0].items()):
                print(f"连续 {count} 次: {freq} 次")

        # 打印双数（偶数）的统计结果
        print(f"{col}大数连续出现次数：")
        if result[1]:
            for count, freq in sorted(result[1].items()):
                print(f"连续 {count} 次: {freq} 次")


if __name__ == '__main__':
    main()
