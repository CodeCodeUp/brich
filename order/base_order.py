import time
import random
import requests
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text  # 添加text导入
import threading
import logging


fib_sequence = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377]
# Cookie 信息
cookies = {
    'visitor_id': '1ac06ae0-7dab-4bac-80cb-b56b8312a809',
    '_ga': 'GA1.1.1712049269.1739547486',
    '_ga_FLS6PM8998': 'GS1.1.1743697081.83.1.1743697103.0.0.0',
    'SessionId': 'de29c1a4-a8d8-49cb-a31a-f53be744a9fa'
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


def is_order_now():
    engine = create_engine('mysql+pymysql://root:202358hjq@116.205.244.106:3306/brich')
    query = "SELECT count(1) FROM auto_order WHERE nextOrder = 0 OR isFinish = 0"
    df = pd.read_sql(query, engine)
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


def get_base_data(data_type):
    engine = create_engine('mysql+pymysql://root:202358hjq@116.205.244.106:3306/brich')
    query = """
        SELECT * 
        FROM base_data 
        WHERE `type` = %(data_type)s 
        ORDER BY id DESC limit 8
    """
    df = pd.read_sql(query, engine, params={
        'data_type': data_type
    })
    # 类型转换...
    return df


def execute_api_request(data):
    url = 'https://www.ub8.com/ajax/board-game/order'

    try:
        response = requests.post(url, json=data, cookies=cookies)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        logging.error(f"请求接口时出错: {e}")
        return False


def insert_data(request_id, draw_type, draw_number, stake, pick, dice_multiplier, base, draw_total):
    engine = create_engine('mysql+pymysql://root:202358hjq@116.205.244.106:3306/brich')
    try:
        with engine.begin() as conn:
            # 使用 text 函数将 SQL 字符串包装成可执行对象
            logging.info(f"开始执行插入操作: {request_id}")
            query = text("""
                            INSERT INTO auto_order (requestId, drawType, drawNumber, stake, pick, base, diceMultiplier, total)
                            SELECT :request_id, :draw_type, :draw_number, :stake, :pick, :base, :dice_multiplier, :total
                            FROM DUAL
                            WHERE NOT EXISTS (
                                SELECT 1 FROM auto_order
                                WHERE drawType = :draw_type AND drawNumber = :draw_number AND pick = :pick
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
                'total': draw_total
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
                bet = int(row["stake"]) * fib_sequence[int(row["base"])]
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
                    draw_total = int(draw_total) + (int(draw_stake) * fib_sequence[int(draw_base)] * 2)
                    draw_base = max(0, draw_base - 2)
                else:
                    draw_base = draw_base + 1
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
                if int(draw_total) >= (2000 + int(row["stake"]) * 3):
                    logging.info("完成此次下单")
                    continue
                num = str(int(draw_number[8:]) + 1).zfill(4)
                # 数据库读取最新的requestId
                df_request_id = pd.read_sql(query_request_id, engine)
                # 16进制+1
                request_id = str(hex(int(df_request_id['requestId'].tolist()[0], 16) + 1))[2:]
                insert_data(request_id, draw_type, f"{draw_number[:8]}-{num}",
                            draw_stake, draw_pick, 1, draw_base, draw_total)
                logging.info(f"插入下一条数据成功, requestId: {request_id}, drawNumber: {draw_number[:8]}-{num}")
        except Exception as e:
            logging.error(f"process_un_finish: {e}")
        time.sleep(5)


def process_do_order():
    while True:
        if is_order_now():
            logging.info("当前有订单正在进行，跳过本次插入")
            return
        df = get_base_data(6)
        if df.empty:
            return
        data = df['number_four'].tolist()
        # 如果全部is_SB_B或is_SB_S且没有正在进行的,插入auto_order数据，pick相反
        if all(is_SB_B(int(num)) for num in data):
            pick = 'SMALL'
            logging.info(f"当前数据全部为大: {data}")
        elif all(is_SB_S(int(num)) for num in data):
            pick = 'BIG'
            logging.info(f"当前数据全部为小: {data}")
        else:
            continue
        # 获取最新的requestId
        request_id = get_request_id()
        draw_type = 'F1TB'
        # draw_number 为最后一个nid+1
        number = df['nid'].tolist()[0]
        num = str(int(number[8:]) + 1).zfill(4)
        draw_number = f"{number[:8]}-{num}"
        stake = 5
        base = 0
        dice_multiplier = 1
        draw_total = 2000
        insert_data(request_id, draw_type, draw_number, stake, pick, dice_multiplier, base, draw_total)
        time.sleep(5)


def keep_alive():
    url = 'https://www.ub8.com/ajax/wallet/main-wallet-balance'
    while True:
        # 随机生成 1 - 20 分钟的时间（单位：秒）
        random_minutes = random.randint(1, 20)
        random_seconds = random_minutes * 60
        logging.info(f"将在 {random_minutes} 分钟后发送下一次请求...")
        time.sleep(random_seconds)
        try:
            response = requests.get(url, cookies=cookies)
            # 打印响应状态码和内容
            logging.info(f"请求保活内容: {response.text}")
        except requests.RequestException as e:
            logging.error(f"请求保活错误: {e}")


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
    thread3 = threading.Thread(target=process_do_order)
    thread4 = threading.Thread(target=keep_alive)
    thread1.start()
    thread2.start()
    thread3.start()
    thread4.start()


