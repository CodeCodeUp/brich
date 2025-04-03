import time
import requests
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text  # 添加text导入
import threading
import logging

fib_sequence = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377]


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


def execute_api_request(data):
    url = 'https://www.ub8.com/ajax/board-game/order'
    # 设置cookie visitor_id=5273c9a8-a40b-4e2c-b516-4e936dd1dc6f; _ga=GA1.1.56548488.1740960454; _ga_FLS6PM8998=GS1.1.1743659039.2.1.1743659095.0.0.0
    cookies = {
        'visitor_id': '5273c9a8-a40b-4e2c-b516-4e936dd1dc6f',
        '_ga': 'GA1.1.56548488.1740960454',
        '_ga_FLS6PM8998': 'GS1.1.1743659039.2.1.1743659095.0.0.0'
    }
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
        with engine.connect() as connection:
            # 使用 text 函数将 SQL 字符串包装成可执行对象
            query = text("""
                INSERT INTO auto_order (requestId, drawType, drawNumber, stake, pick, base, diceMultiplier, total)
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
                'base': base,
                'dice_multiplier': dice_multiplier,
                'total': draw_total
            })
            connection.commit()
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
                    "diceMultiplier": row["diceMultiplier"],
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
                if is_SB_B(int(value)):
                    value = 'BIG'
                elif is_SB_S(int(value)):
                    value = 'SMALL'
                else:
                    value = 'DRAW'
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
                    continue
                num = str(int(draw_number[8:]) + 1).zfill(4)
                # 数据库读取最新的requestId
                df_request_id = pd.read_sql(query_request_id, engine)
                # 16进制+1
                request_id = str(hex(int(df_request_id['requestId'].tolist()[0], 16) + 1))[2:]
                insert_data(request_id, draw_type, f"{draw_number[:8]}-{num}",
                            draw_stake, draw_pick, 1, draw_base, draw_total)
        except Exception as e:
            logging.error(f"process_un_finish: {e}")
        time.sleep(5)


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
    thread1.start()
    thread2.start()


