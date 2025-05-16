import pandas as pd
from sqlalchemy import create_engine


# 创建SQLAlchemy数据库连接引擎
def get_data():
    engine = create_engine('mysql+pymysql://root:202358hjq@116.205.244.106:3306/brich')

    # SELECT * FROM base_data WHERE `type` = 2  and nid >= 202503230001 and nid<202503240001 and insert_time > '2025-02-17' order by id
    # 查询数据
    query = ("SELECT * FROM base_data WHERE `type` = 6  "
             "and insert_time between '2025-05-15' and '2025-05-20'")
    df = pd.read_sql(query, engine)

    # 将number_one到number_five列转换为数值类型
    for col in ['number_one', 'number_two', 'number_three', 'number_four', 'number_five', 'total']:
        df[col] = pd.to_numeric(df[col], errors='coerce')  # 无法转换的会变成NaN

    return df
