import time
import random
import requests
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text  # 添加text导入
import threading
import logging


fib_sequence = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377]
# Cookie 信息
cookies = {
    'visitor_id': '83bd163c-e1ed-4623-a3ae-66e7858b860d',
    '_ga': 'GA1.1.571452156.1745314369',
    '_ga_FLS6PM8998': 'GS1.1.1745401141.2.1.1745401470.0.0.0',
    'SessionId': '6e218735-5c6d-4bf5-aa72-48dd1f3616e7'
}


def is_SB_B(num):
    if 11 <= num <= 17:
        return True
    else:
        return False


def is_SB_S(num):
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


def is_order_now(draw_type, pick, strategy_type):
    engine = create_engine('mysql+pymysql://root:202358hjq@116.205.244.106:3306/brich')
    query = ("SELECT count(1) FROM auto_order WHERE  drawType = %s AND pick = %s AND type = %s AND"
             "(nextOrder = 0 OR isFinish = 0)")
    df = pd.read_sql(query, engine, params=(draw_type, pick, strategy_type))
    if df.empty:
        return False
    count = df.iloc[0, 0]
    if count > 0:
        return True
    else:
        return False


def get_request_id():
    engine = create_engine('mysql+pymysql://root:202358hjq@116.205.244.106:3306/brich')
    query = "SELECT requestId FROM auto_order WHERE id = (SELECT MAX(id) FROM auto_order)"
    df_request_id = pd.read_sql(query, engine)
    if df_request_id.empty:
        return '195f6cc06a7'
    # 16进制+1
    last_request_id = str(hex(int(df_request_id['requestId'].tolist()[0], 16) + 1))[2:]
    return last_request_id


def get_base_data(data_type, limit):
    engine = create_engine('mysql+pymysql://root:202358hjq@116.205.244.106:3306/brich')
    query = """
        SELECT * 
        FROM base_data 
        WHERE `type` = %(data_type)s 
        ORDER BY id DESC limit %(limit)s
    """
    df = pd.read_sql(query, engine, params={
        'data_type': data_type
        , 'limit': limit
    })
    # 类型转换...
    return df


def execute_api_request(data):
    url = 'https://www.goub88.com/ajax/board-game/order'

    try:
        response = requests.post(url, json=data, cookies=cookies)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        logging.error(f"请求接口时出错: {e}")
        return False


def insert_data(request_id, draw_type, draw_number, stake, pick, dice_multiplier, base, draw_total, strategy_type):
    engine = create_engine('mysql+pymysql://root:202358hjq@116.205.244.106:3306/brich')
    try:
        with engine.begin() as conn:
            # 使用 text 函数将 SQL 字符串包装成可执行对象
            logging.info(f"开始执行插入操作: {request_id}")
            query = text("""
                            INSERT INTO auto_order (requestId, drawType, drawNumber,
                             stake, pick, base, diceMultiplier, total, type)
                            SELECT :request_id, :draw_type, :draw_number, 
                            :stake, :pick, :base, :dice_multiplier, :total, :type
                            FROM DUAL
                            WHERE NOT EXISTS (
                                SELECT 1 FROM auto_order
                                WHERE drawType = :draw_type AND drawNumber = :draw_number 
                                AND pick = :pick AND type = :type
                            )
                        """)

            conn.execute(query, {
                'request_id': request_id,
                'draw_type': draw_type,
                'draw_number': draw_number,
                'stake': stake,
                'pick': pick,
                'base': base,
                'dice_multiplier': dice_multiplier,
                'total': draw_total,
                'type': strategy_type
            })
            logging.info(f"插入成功: {request_id}")

    except Exception as e:
        logging.error(f"insert_data: {e}")


def process_un_orders():
    engine = create_engine('mysql+pymysql://root:202358hjq@116.205.244.106:3306/brich')
    while True:
        try:
            query = "SELECT * FROM auto_order WHERE nextOrder = 0 AND isFinish = 0"
            df = pd.read_sql(query, engine)

            for _, row in df.iterrows():
                total = row["total"]
                strategy_type = row["type"]
                bet = 0
                if strategy_type == 1:
                    bet = int(row["stake"]) * fib_sequence[int(row["base"])]
                if strategy_type == 2:
                    bet = int(row["stake"]) * int(row["base"])
                data = {
                    "requestId": row["requestId"],
                    "drawType": row["drawType"],
                    "drawNumber": row["drawNumber"],
                    "orderItems": [{"stake": bet, "pick": row["pick"]}],
                    "diceMultiplier": int(row["diceMultiplier"]),
                    "categoryPrize": row["categoryPrize"]
                }
                logging.info(f"处理订单 {row['requestId']}，请求数据: {data}")
                if execute_api_request(data):
                    # 使用连接对象和参数化查询
                    with engine.begin() as conn:  # 自动提交事务
                        update_query = text("""
                            UPDATE auto_order 
                            SET nextOrder = 1, 
                                update_time = NOW() ,
                                total = :total
                            WHERE id = :id
                        """)
                        conn.execute(update_query, {"id": row['id'], "total": int(total) - bet})

                    logging.info(f"处理订单 {row['requestId']} 成功")
                else:
                    logging.error(f"处理订单 {row['requestId']} 失败")
                    # 更新数据库中的状态
                    with engine.begin() as conn:
                        update_query = text("""
                            UPDATE auto_order 
                            SET nextOrder = 1, 
                                isFinish = 1,
                                update_time = NOW() 
                            WHERE id = :id
                        """)
                        conn.execute(update_query, {"id": row['id']})

        except Exception as e:
            logging.error(f"process_un_orders: {e}")

        time.sleep(5)


def process_un_finish():
    engine = create_engine('mysql+pymysql://root:202358hjq@116.205.244.106:3306/brich')
    while True:
        try:
            query = "SELECT * FROM auto_order WHERE nextOrder = 1 AND isFinish = 0"
            query_last = "SELECT * FROM base_data WHERE type = %s AND nid = %s"
            query_request_id = "SELECT requestId FROM auto_order WHERE id = (select max(id) from auto_order)"
            df = pd.read_sql(query, engine)

            for _, row in df.iterrows():
                draw_type = row["drawType"]
                draw_number = row["drawNumber"].replace('-', '')
                draw_pick = row["pick"]
                draw_stake = row["stake"]
                draw_base = int(row["base"])
                draw_total = row["total"]
                strategy_type = row["type"]
                df_last = pd.read_sql(query_last, engine, params=(6, draw_number))
                if df_last.empty:
                    continue
                value = df_last['number_four'].tolist()[0]
                logging.info(f"draw_pick {draw_pick}，value: {value}")
                if draw_pick == 'BIG' or draw_pick == 'SMALL':
                    if is_SB_B(int(value)):
                        value = 'BIG'
                    elif is_SB_S(int(value)):
                        value = 'SMALL'
                    else:
                        value = 'DRAW'
                elif draw_pick == 'EVEN' or draw_pick == 'ODD':
                    if is_D(int(value)):
                        value = 'EVEN'
                    elif is_O(int(value)):
                        value = 'ODD'
                    else:
                        value = 'DRAW'
                else:
                    logging.error(f"未知的类型: {draw_pick}")
                    return
                logging.info(f"draw_pick {draw_pick}，value: {value}")
                if value == draw_pick:
                    if strategy_type == 1:
                        draw_total = int(draw_total) + (int(draw_stake) * fib_sequence[int(draw_base)] * 2)
                        draw_base = max(0, draw_base - 2)
                    if strategy_type == 2:
                        draw_total = int(draw_total) + (int(draw_stake) * int(draw_base) * 2)
                else:
                    if strategy_type == 1:
                        draw_base = draw_base + 1
                    if strategy_type == 2:
                        draw_base = draw_base * 2
                with engine.begin() as conn:  # 自动提交事务
                    update_query = text("""
                        UPDATE auto_order 
                        SET nextOrder = 1, 
                            isFinish = 1,
                            total = :total,
                            update_time = NOW() 
                        WHERE id = :id
                    """)
                    conn.execute(update_query, {"id": row['id'], "total": draw_total})
                if strategy_type == 1:
                    if int(draw_total) >= (2000 + int(row["stake"]) * 3) or int(draw_total) < 0:
                        logging.info("类型1，完成此次下单")
                        continue
                if strategy_type == 2:
                    if int(draw_total) >= (2000 + int(row["stake"])) or int(draw_base) > 4 or int(draw_total) < 0:
                        logging.info("类型2，完成此次下单")
                        continue
                num = str(int(draw_number[8:]) + 1).zfill(4)
                # 数据库读取最新的requestId
                df_request_id = pd.read_sql(query_request_id, engine)
                # 16进制+1
                request_id = str(hex(int(df_request_id['requestId'].tolist()[0], 16) + 1))[2:]
                insert_data(request_id, draw_type, f"{draw_number[:8]}-{num}",
                            draw_stake, draw_pick, 1, draw_base, draw_total, strategy_type)
                logging.info(f"插入下一条数据成功, requestId: {request_id}, drawNumber: {draw_number[:8]}-{num}")
        except Exception as e:
            logging.error(f"process_un_finish: {e}")
        time.sleep(5)


def process_do_order(data_type, limit, order, pick, stake_num=5):
    while True:
        df = get_base_data(data_type, limit)
        if df.empty:
            time.sleep(20)
            continue
        data = df['number_four'].tolist()
        # 如果全部is_SB_B或is_SB_S且没有正在进行的,插入auto_order数据，pick相反
        if all(order(int(num)) for num in data):
            logging.info(f"当前数据全部为{pick}: {data}")
        else:
            time.sleep(20)
            continue
        if is_order_now('F1TB', pick, 1):
            logging.info("当前有订单正在进行，跳过本次插入")
            time.sleep(20)
            continue
        # 获取最新的requestId
        request_id = get_request_id()
        draw_type = 'F1TB'
        # draw_number 为最后一个nid+1
        number = df['nid'].tolist()[0]
        num = str(int(number[8:]) + 1).zfill(4)
        draw_number = f"{number[:8]}-{num}"
        stake = stake_num
        base = 0
        dice_multiplier = 1
        draw_total = 2000
        insert_data(request_id, draw_type, draw_number, stake, pick, dice_multiplier, base, draw_total, 1)
        time.sleep(30)


def process_do_order_two():
    while True:
        length = 8
        df = get_base_data(6, length)
        # 切分为前七个和最后一个
        if df.empty:
            time.sleep(20)
            continue
        if len(df) < length:
            time.sleep(20)
            continue
        data = df['number_four'].tolist()
        before = length - 1
        # 前七个
        data_before = data[:before]
        # 后一个
        data_1 = data[-1]
        stake = 10
        # 如果前七个和最后一个不同且没有正在进行的,插入auto_order数据，pick相反
        # if all(is_SB_B(int(num)) for num in data_before) and not is_SB_B(int(data_1)):
        #     stake = 5
        #     pick = 'SMALL'
        #     logging.info(f"当前数据全部为大: {data}")
        if all(is_SB_S(int(num)) for num in data_before) and not is_SB_S(int(data_1)):
            stake = 10
            pick = 'BIG'
            logging.info(f"当前数据全部为小: {data}")
        # elif all(is_D(int(num)) for num in data_before) and not is_D(int(data_1)):
        #     pick = 'ODD'
        #     logging.info(f"当前数据全部为偶: {data}")
        # elif all(is_O(int(num)) for num in data_before) and not is_O(int(data_1)):
        #     pick = 'EVEN'
        #     logging.info(f"当前数据全部为奇: {data}")
        else:
            time.sleep(20)
            continue
        if is_order_now('F1TB', pick, 2):
            logging.info("当前有订单正在进行，跳过本次插入")
            time.sleep(20)
            continue
        # 获取最新的requestId
        request_id = get_request_id()
        draw_type = 'F1TB'
        # draw_number 为最后一个nid+1
        number = df['nid'].tolist()[0]
        num = str(int(number[8:]) + 1).zfill(4)
        draw_number = f"{number[:8]}-{num}"
        base = 1
        dice_multiplier = 1
        draw_total = 2000
        insert_data(request_id, draw_type, draw_number, stake,
                    pick, dice_multiplier, base, draw_total, 2)
        time.sleep(30)


def keep_alive():
    url = 'https://www.goub88.com/ajax/wallet/main-wallet-balance'
    while True:
        # 随机生成 1 - 20 分钟的时间（单位：秒）
        try:
            response = requests.get(url, cookies=cookies)
            # 打印响应状态码和内容
            logging.info(f"请求保活内容: {response.text}")
        except requests.RequestException as e:
            logging.error(f"请求保活错误: {e}")
        random_seconds = random.randint(1 * 60, 20 * 60)
        logging.info(f"将在 {random_seconds} s后发送下一次请求...")
        time.sleep(random_seconds)


if __name__ == "__main__":
    # 配置日志系统
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("lottery_monitor.log"),
            logging.StreamHandler()
        ]
    )
    # 异步执行两个函数
    thread1 = threading.Thread(target=process_un_orders)
    thread2 = threading.Thread(target=process_un_finish)
    thread4 = threading.Thread(target=keep_alive)
    thread1.start()
    thread2.start()
    thread4.start()
    thread5 = threading.Thread(target=process_do_order_two)
    thread5.start()
    thread3 = threading.Thread(target=process_do_order, args=(6, 9, is_SB_B, 'SMALL', 4))
    thread3.start()
    thread6 = threading.Thread(target=process_do_order, args=(6, 9, is_SB_S, 'BIG', 4))
    thread6.start()
    thread7 = threading.Thread(target=process_do_order, args=(6, 10, is_D, 'ODD', 5))
    thread7.start()
    thread8 = threading.Thread(target=process_do_order, args=(6, 10, is_O, 'EVEN', 5))
    thread8.start()



