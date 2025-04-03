import streamlit as st
import pandas as pd
import datetime
from datetime import timedelta
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from probability_calculator import ProbabilityCalculator
from strategy_big_small import calculate_big_small_statistics
from strategy_consecutive import calculate_consecutive_big_small
from statistics_odd_even import calculate_odd_even
from statistics_big_small_continue import analyze_data
from times_odd_even import count_consecutive_odds_evens
from statistics_sb_data import get_result
from statistics_sb_data import get_ds_result
from statistics_sb_data import count_sb_odds_evens


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


def stop_order():
    engine = create_engine('mysql+pymysql://root:202358hjq@116.205.244.106:3306/brich')
    query = text("UPDATE auto_order SET nextOrder = 1, isFinish = 1")
    try:
        # 使用 engine.begin() 自动管理事务
        with engine.begin() as connection:
            connection.execute(query)
        st.success("操作成功！")
    except Exception as e:
        st.error(f"操作失败: {str(e)}")


# 数据获取函数（增加参数）
def get_base_data(data_type, start_time, end_time):
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


def get_order_data(data_type):
    engine = create_engine('mysql+pymysql://root:202358hjq@116.205.244.106:3306/brich')
    query = """
        SELECT * 
        FROM base_data 
        WHERE `type` = %(data_type)s 
        ORDER BY id DESC limit 1
    """
    df = pd.read_sql(query, engine, params={
        'data_type': data_type,
    })
    # 类型转换...
    return df


def insert_data(request_id, draw_type, draw_number, stake, pick, dice_multiplier):
    engine = create_engine('mysql+pymysql://root:202358hjq@116.205.244.106:3306/brich')
    try:
        with engine.connect() as connection:
            # 使用 text 函数将 SQL 字符串包装成可执行对象
            query = text("""
                            INSERT INTO auto_order 
                            (requestId, drawType, drawNumber, stake, pick, base, diceMultiplier, total)
                            SELECT :request_id, :draw_type, :draw_number, :stake, :pick, :base, :dice_multiplier, :total
                            FROM DUAL
                            WHERE NOT EXISTS (
                                SELECT 1 FROM auto_order
                                WHERE drawType = :draw_type AND drawNumber = :draw_number
                            )
                        """)
            connection.execute(query, {
                'request_id': request_id,
                'draw_type': draw_type,
                'draw_number': draw_number,
                'stake': stake,
                'pick': pick,
                'base': '0',
                'dice_multiplier': dice_multiplier,
                'total': '2000'
            })
            connection.commit()
            st.success("数据插入成功！")
    except IntegrityError:
        st.warning("数据已存在，未插入！")
    except Exception as e:
        st.error(f"插入数据时出错: {e}")


def get_request_id():
    engine = create_engine('mysql+pymysql://root:202358hjq@116.205.244.106:3306/brich')
    query = "SELECT requestId FROM auto_order WHERE id = (SELECT MAX(id) FROM auto_order)"
    df_request_id = pd.read_sql(query, engine)
    if df_request_id.empty:
        return '195f6cc06a7'
    # 16进制+1
    last_request_id = str(hex(int(df_request_id['requestId'].tolist()[0], 16) + 1))[2:]
    return last_request_id


def main():
    # 设置默认时间策略
    # ---------------------------------------------------
    # 默认起始时间 = 3天前
    default_start = datetime.date.today()

    # 默认结束时间 = 明天（开始时间次日）
    default_end = datetime.date.today() + timedelta(days=1)
    st.title("Spring Ai")

    with st.sidebar:
        data_type = st.selectbox("选择数据类型", [1, 2, 3, 4, 5, 6, 7], index=1)
        start_time = st.date_input(
            label="📅 开始时间",
            value=default_start,  # 设置默认值
            min_value=datetime.date(2020, 1, 1),  # 可选最早日期
            max_value=datetime.date.today(),  # 可选最晚日期（不能选未来）
            key="start_date"  # 唯一标识符
        )
        # 自动计算最小可选结束时间（开始时间次日）
        min_end_date = start_time + timedelta(days=1)
        end_time = st.date_input(
            label="📅 结束时间",
            value=default_end,  # 默认设置为明天
            min_value=datetime.date(2020, 1, 1),  # 禁止早于开始时间
            max_value=datetime.date.today() + timedelta(days=1),
            key="end_date"
        )
        data_num = st.selectbox("选择统计数量", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], index=3)
        order_data = get_order_data(data_type)
        number = order_data['nid'].tolist()[0]
        request_id = st.text_input("requestId", get_request_id())
        draw_type = st.text_input("drawType", "F1TB")
        num = str(int(number[8:]) + 1).zfill(4)
        draw_number = st.text_input("drawNumber", f"{number[:8]}-{num}")
        stake = st.text_input("stake", 5)
        index = 0 if is_S(int(order_data['number_four'].tolist()[0])) else 1
        pick = st.selectbox("pick", ['BIG', 'SMALL'], index=index)
        dice_multiplier = st.text_input("diceMultiplier", 1)
        if st.button("SAVE"):
            insert_data(request_id, draw_type, draw_number, stake, pick, dice_multiplier)
        if st.button("STOP"):
            stop_order()

    st.button('DEL')
    if data_type in [6, 7]:
        df = get_base_data(data_type, start_time, end_time)
        if df.empty:
            st.warning("没有找到指定时间段的数据。")
            st.stop()  # 停止执行后续代码
        # 修正方案：将结果转换为 DataFrame
        result = pd.DataFrame(
            get_result(df['number_four'].tolist()),
            columns=['pattern']  # 添加列名
        )
        # 添加 count 列示例（根据你的实际数据结构调整）
        result['count'] = result['pattern'].apply(len)
        result = result[::-1].reset_index(drop=True)
        ds_result = pd.DataFrame(
            get_ds_result(df['number_four'].tolist()),
            columns=['pattern']  # 添加列名
        )
        # 添加 count 列示例（根据你的实际数据结构调整）
        ds_result['count'] = ds_result['pattern'].apply(len)
        ds_result = ds_result[::-1].reset_index(drop=True)
        with st.expander("🔍 B/S s", expanded=True):
            col1, col2 = st.columns([4, 1])

            with col1:
                # 确保 result 是 DataFrame
                if isinstance(result, list):  # 如果原始结果是列表
                    result = pd.DataFrame(result, columns=['pattern'])

                # 添加样式
                styled_result = result.style \
                    .map(lambda x: "color: green" if "D" in x else "color: red", subset=['pattern']) \
                    .set_properties(**{
                    'font-size': '16px',
                    'text-align': 'center'
                })

                st.dataframe(styled_result, use_container_width=True)

            # 右侧添加统计指标
            with col2:
                # 统计每个模式中'D'的出现次数
                d_count = result['pattern'].str.count('D').sum()
                s_count = result['pattern'].str.count('s').sum()
                # 统计总字符数（所有模式长度之和）
                total_chars = result['pattern'].str.len().sum()
                # 计算'D'的概率（保留两位小数）
                d_prob = round((d_count / total_chars) * 100, 2)
                s_prob = round((s_count / total_chars) * 100, 2)
                st.metric("long", f"{result['count'].max()} ")
                st.metric("D", f"{d_prob} ")
                st.metric("s", f"{s_prob} ")
        with st.expander("🔍 S/o s", expanded=True):
            col1, col2 = st.columns([4, 1])

            with col1:
                # 确保 result 是 DataFrame
                if isinstance(ds_result, list):  # 如果原始结果是列表
                    ds_result = pd.DataFrame(ds_result, columns=['pattern'])

                # 添加样式
                styled_result = ds_result.style \
                    .map(lambda x: "color: green" if "S" in x else "color: red", subset=['pattern']) \
                    .set_properties(**{
                    'font-size': '16px',
                    'text-align': 'center'
                })

                st.dataframe(styled_result, use_container_width=True)

            # 右侧添加统计指标
            with col2:
                # 统计每个模式中'D'的出现次数
                d_count = ds_result['pattern'].str.count('S').sum()
                s_count = ds_result['pattern'].str.count('o').sum()
                # 统计总字符数（所有模式长度之和）
                total_chars = ds_result['pattern'].str.len().sum()
                # 计算'D'的概率（保留两位小数）
                d_prob = round((d_count / total_chars) * 100, 2)
                s_prob = round((s_count / total_chars) * 100, 2)
                st.metric("long", f"{ds_result['count'].max()} ")
                st.metric("S", f"{d_prob} ")
                st.metric("o", f"{s_prob} ")
        with st.container():
            # 直接创建五个等宽列
            cols = st.columns(1)

            # 配置每列显示的内容
            column_items = [
                'number_four'
            ]

            # 遍历五列
            for idx, col in enumerate(cols):
                with col:
                    item = column_items[idx]
                    with st.expander(f"🔁  B/S", expanded=False):
                        result = count_sb_odds_evens(df[item].tolist())

                        # 紧凑型布局
                        cols_inner = st.columns(2)

                        # 单数统计
                        with cols_inner[0]:
                            st.caption(f"**S**")
                            if result[0]:
                                for count, freq in sorted(result[0].items()):
                                    # Normalize freq to ensure it's within [0.0, 1.0]
                                    normalized_freq = min(freq / 100, 1.0)
                                    st.progress(normalized_freq, text=f"{count}: {freq}s")

                        # 双数统计
                        with cols_inner[1]:
                            st.caption(f"**B**")
                            if result[1]:
                                for count, freq in sorted(result[1].items()):
                                    # Normalize freq to ensure it's within [0.0, 1.0]
                                    normalized_freq = min(freq / 100, 1.0)
                                    st.progress(normalized_freq, text=f"{count}: {freq}s")

    else:
        with st.spinner("分析中..."):
            df = get_base_data(data_type, start_time, end_time)
            if df.empty:
                st.warning("没有找到指定时间段的数据。")
                st.stop()  # 停止执行后续代码
            # 类型转换...
            for col in ['number_one', 'number_two', 'number_three', 'number_four', 'number_five', 'total']:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # 使用折叠容器包裹每个分析模块
            with st.expander("🔍 B/S s", expanded=True):
                statistics = calculate_big_small_statistics(df, ['number_one', 'number_two', 'number_three',
                                                                 'number_four', 'number_five'])
                st.dataframe(statistics)

            with st.expander("📈 B/S  long s", expanded=False):
                consecutive_stats = calculate_consecutive_big_small(df, ['number_one', 'number_two',
                                                                         'number_three', 'number_four',
                                                                         'number_five'])
                st.table(consecutive_stats)

            with st.expander("🔢 O/E s", expanded=False):
                calculate_data = calculate_odd_even(df, ['number_one', 'number_two',
                                                         'number_three', 'number_four',
                                                         'number_five'])
                st.dataframe(calculate_data.style.highlight_max(axis=0))

            with st.expander("🎲 N s", expanded=False):
                probability_calculator = ProbabilityCalculator(df,
                                                               ['number_one', 'number_two',
                                                                'number_three', 'number_four',
                                                                'number_five'])
                result = probability_calculator.print_probability()
                st.write(result[0])
                st.write(result[1])

            with st.expander("📊 B/S long t", expanded=False):
                st.subheader('B/S long t')
                for col in ['number_one', 'number_two', 'number_three',
                            'number_four', 'number_five']:
                    with st.container():
                        data = analyze_data(df[col].tolist(), data_num)
                        st.code(f"{col}: {data}")

            with st.container():
                # 直接创建五个等宽列
                cols = st.columns(5)

                # 配置每列显示的内容
                column_items = [
                    'number_one',
                    'number_two',
                    'number_three',
                    'number_four',
                    'number_five'
                ]

                # 遍历五列
                for idx, col in enumerate(cols):
                    with col:
                        item = column_items[idx]
                        with st.expander(f"🔁 {item} B/S", expanded=False):
                            result = count_consecutive_odds_evens(df[item].tolist())

                            # 紧凑型布局
                            cols_inner = st.columns(1)

                            # 单数统计
                            with cols_inner[0]:
                                st.caption(f"**S**")
                                if result[0]:
                                    for count, freq in sorted(result[0].items()):
                                        # Normalize freq to ensure it's within [0.0, 1.0]
                                        normalized_freq = min(freq / 100, 1.0)
                                        st.progress(normalized_freq, text=f"{count}: {freq}s")

                            # 双数统计
                            with cols_inner[0]:
                                st.caption(f"**B**")
                                if result[1]:
                                    for count, freq in sorted(result[1].items()):
                                        # Normalize freq to ensure it's within [0.0, 1.0]
                                        normalized_freq = min(freq / 100, 1.0)
                                        st.progress(normalized_freq, text=f"{count}: {freq}s")


if __name__ == "__main__":
    main()
