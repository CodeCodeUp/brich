import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from probability_calculator import ProbabilityCalculator
from get_data import get_data
from strategy_big_small import calculate_big_small_statistics
from strategy_consecutive import calculate_consecutive_big_small
from statistics_odd_even import calculate_odd_even
from statistics_big_small_continue import analyze_data
from times_odd_even import count_consecutive_odds_evens

# 数据获取函数（增加参数）
def get_data(data_type, start_time, end_time):
    engine = create_engine('mysql+pymysql://root:202358hjq@116.205.244.106:3306/brich')
    query = """
        SELECT * 
        FROM base_data 
        WHERE `type` = %(data_type)s 
        AND insert_time BETWEEN %(start_time)s AND %(end_time)s 
        ORDER BY id
    """
    df = pd.read_sql(query, engine, params={
        'data_type': data_type,
        'start_time': start_time,
        'end_time': end_time
    })
    # 类型转换...
    return df

# 网页界面
def main():
    st.title("数据分析平台")

    # 侧边栏参数选择
    with st.sidebar:
        data_type = st.selectbox("选择数据类型", [1, 2, 3, 4, 5], index=1)
        start_time = st.date_input("开始时间")
        end_time = st.date_input("结束时间")

    # 查询数据
    if st.button("开始分析"):
        with st.spinner("分析中..."):
            df = get_data(data_type, start_time, end_time)
            # 将number_one到number_five列转换为数值类型
            for col in ['number_one', 'number_two', 'number_three', 'number_four', 'number_five', 'total']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            # 直接展示结果（自动转网页格式）
            st.subheader("大小概率")
            # 计算“大”和“小”的规律
            statistics = calculate_big_small_statistics(df, ['number_one', 'number_two', 'number_three', 'number_four',
                                                             'number_five'])
            st.write(statistics)  # 自动识别DataFrame/字典格式

            st.subheader("连续出现统计")
            consecutive_stats = calculate_consecutive_big_small(df, ['number_one', 'number_two', 'number_three',
                                                                     'number_four',
                                                                     'number_five'])
            st.table(consecutive_stats)  # 表格展示

            # 更多分析结果...
            st.subheader("单双概率")
            calculate_data = calculate_odd_even(df, ['number_one', 'number_two', 'number_three', 'number_four',
                                                     'number_five'])
            # 统计连续单/双超过4次的次数，连续单双超过4次且不超过7次的次数，连续单双7次的次数

            st.write(calculate_data.style)

            st.subheader("统计每个数字的概率")
            probability_calculator = ProbabilityCalculator(df,
                                                           ['number_one', 'number_two', 'number_three', 'number_four',
                                                            'number_five'])
            result = probability_calculator.print_probability()
            st.subheader("每列数字出现次数：")
            st.write(result[0])
            st.subheader("\n每列数字出现概率：")
            st.write(result[1])

            st.subheader('# 统计大小总的连续情况')
            for col in ['number_one', 'number_two', 'number_three', 'number_four', 'number_five']:
                data = analyze_data(df[col].tolist())
                st.write(f"{col}:{data}")

            st.subheader('统计 大/小 连续出现n次的次数')
            for col in ['number_one', 'number_two', 'number_three', 'number_four', 'number_five']:
                result = count_consecutive_odds_evens(df[col].tolist())
                # 打印单数（奇数）的统计结果
                st.subheader(f"{col}小数连续出现次数：")
                if result[0]:
                    for count, freq in sorted(result[0].items()):
                        st.write(f"连续 {count} 次: {freq} 次")

                # 打印双数（偶数）的统计结果
                st.subheader(f"{col}大数连续出现次数：")
                if result[1]:
                    for count, freq in sorted(result[1].items()):
                        st.write(f"连续 {count} 次: {freq} 次")


if __name__ == "__main__":
    main()