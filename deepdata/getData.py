import requests
from datetime import datetime
from sqlalchemy import create_engine, text
import json

# 初始化 session 并设置 cookie
session = requests.Session()
session.cookies.set('visitor_id', 'bef8e599-0bc7-4305-8dfa-228b1eb71ed5')

# 获取数据 # https://www.ub8.com/ajax/draw/TWBSSC/result?numOfDraw=3000
# https://www.ub8.com/ajax/draw/ASHAREF2SSC/result?numOfDraw=3000
response = session.get('https://www.ub8.com/ajax/draw/TWBSSC/result?numOfDraw=3000')
data = response.json()

# # 读取配置文件
# with open("data.config", "r", encoding="utf-8") as f:
#     data = json.load(f)
# 解析获取到的数据
draw_results = data.get("drawResults", [])

# 使用 SQLAlchemy 连接数据库
engine = create_engine('mysql+pymysql://root:123456@127.0.0.1:3306/brich')

try:
    with engine.connect() as connection:
        # 注意这里使用了 text() 函数包裹SQL语句
        select_max_query = text("SELECT MAX(nid) FROM base_data WHERE type = 1")
        max_nid_result = connection.execute(select_max_query)
        max_nid_row = max_nid_result.fetchone()
        max_nid = int(max_nid_row[0] if max_nid_row[0] is not None else 0)

        # 插入数据的查询
        insert_query = text("""
        INSERT INTO base_data (nid, number_one, number_two, number_three, number_four, number_five, type, insert_time)
        VALUES (:nid, :number_one, :number_two, :number_three, :number_four, :number_five, :type, :insert_time)
        """)

        # 插入数据
        for result in draw_results:
            draw_number = int(result["drawNumber"].replace("-",""))
            if draw_number > max_nid:
                draw_result = [int(num) for num in result["drawResult"]]
                type_value = 1  # 对应的type是1
                insert_time = datetime.now()

                connection.execute(insert_query, {
                    "nid": draw_number,
                    "number_one": draw_result[0],
                    "number_two": draw_result[1],
                    "number_three": draw_result[2],
                    "number_four": draw_result[3],
                    "number_five": draw_result[4],
                    "type": type_value,
                    "insert_time": insert_time
                })
        # 显式提交事务
        connection.commit()
except Exception as e:
    print("An error occurred:", e)
