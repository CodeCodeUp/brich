import requests
from sqlalchemy import create_engine, text
from datetime import datetime

# 定义URL字典
urls = {
    1: 'https://www.ub8.com/ajax/draw/TWBSSC/result?numOfDraw=3000',
    2: 'https://www.ub8.com/ajax/draw/ASHAREF2SSC/result?numOfDraw=3000',
    3: 'https://www.ub8.com/ajax/draw/APF10SSC/result?numOfDraw=3000'
}

# 创建会话对象
session = requests.Session()

# 遍历URL字典
for key, url in urls.items():
    # 发送请求并获取响应
    response = session.get(url)
    data = response.json()

    # 解析获取到的数据
    draw_results = data.get("drawResults", [])

    # 使用 SQLAlchemy 连接数据库
    engine = create_engine('mysql+pymysql://root:123456@127.0.0.1:3306/brich')

    try:
        with engine.connect() as connection:
            # 根据key选择type值
            type_value = key

            # 查询最大nid
            select_max_query = text(f"SELECT MAX(nid) FROM base_data WHERE type = {type_value}")
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
                draw_number = int(result["drawNumber"].replace("-", ""))
                if draw_number > max_nid:
                    draw_result = [int(num) for num in result["drawResult"]]
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
        print(f"An error occurred while processing URL {url}: {e}")