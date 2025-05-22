import logging
from datetime import datetime
import pandas as pd
import akshare as ak
from sqlalchemy import create_engine, text  # 新增导入

# 日志配置
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='price_tracking.log')

# 数据库配置
DB_CONFIG = {
    'host': '116.205.244.106',
    'user': 'root',
    'password': '202358hjq',
    'database': 'stock',
    'charset': 'utf8mb4'
}


# 创建SQLAlchemy引擎
def get_db_engine():
    connection_string = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}"
    return create_engine(connection_string)


# 获取需跟踪的股票及其起始时间（修改SQL部分）
def fetch_stock_list():
    engine = get_db_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT stock_code, begin_time FROM stock_base"))
        df = pd.DataFrame(result.fetchall(), columns=['stock_code', 'begin_time'])
    df['stock_code'] = df['stock_code'].astype(str)
    df['begin_time'] = pd.to_datetime(df['begin_time'])
    return df


# 获取每只股票的最后跟踪时间（修改SQL部分）
def fetch_last_times(codes):
    engine = get_db_engine()
    placeholders = ', '.join([':code_' + str(i) for i in range(len(codes))])
    params = {'code_' + str(i): code for i, code in enumerate(codes)}

    with engine.connect() as conn:
        query = text(f"""
            SELECT stock_code, MAX(track_time) AS last_time 
            FROM stock_price_tracking 
            WHERE stock_code IN ({placeholders}) 
            GROUP BY stock_code
        """)
        result = conn.execute(query, params)
        rows = result.fetchall()

    return {r[0]: r[1] for r in rows}


# 插入行情数据（保持原逻辑不变）
def insert_quote(code, quote):
    for row in quote.itertuples(index=False):
        current_time = pd.Timestamp(row[0])
        if current_time.hour == 10 and current_time.minute == 0:
            new_time = current_time.replace(hour=9, minute=30)
            new_row = [new_time]
            new_row += [row[1]] * 4
            new_row += [0] * 6
            quote.loc[len(quote)] = new_row

    conn = pymysql.connect(**DB_CONFIG)
    cur = conn.cursor()
    sql = ("INSERT INTO stock_price_tracking "
           "(stock_code, track_time, current_price, open_price, high_price, low_price, "
           "volume, amount, change_rate) "
           "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) "
           "ON DUPLICATE KEY UPDATE "
           "current_price=VALUES(current_price), open_price=VALUES(open_price), "
           "high_price=VALUES(high_price), low_price=VALUES(low_price), "
           "volume=VALUES(volume), amount=VALUES(amount), change_rate=VALUES(change_rate)")
    for row in quote.itertuples(index=False):
        try:
            cur.execute(sql, (
                code,
                row[0],
                row[2],
                row[1],
                row[3],
                row[4],
                row[7],
                row[8],
                row[5]
            ))
        except Exception as e:
            logging.error(f"{code} 插入数据异常: {e}")
        finally:
            conn.commit()
    cur.close()


# 获取股票价格数据（保持原逻辑不变）
def get_price(code, begin):
    quote = None
    try:
        quote = ak.stock_zh_a_hist_min_em(symbol=code, period="30", adjust="qfq", start_date=begin)
        if quote is None or len(quote) == 0:
            logging.error(f"{code} 获取数据失败")
            return
        insert_quote(code, quote)
    except Exception as e:
        logging.error(f"{code} 获取数据异常: {e}, 数据: {quote}")


# 主程序（保持原逻辑不变）
if __name__ == '__main__':
    logging.info("开始获取数据")
    now = datetime.now().replace(second=0, microsecond=0)
    stock_df = fetch_stock_list()
    codes = stock_df['stock_code'].tolist()
    last_times = fetch_last_times(codes)
    for code, begin in stock_df.itertuples(index=False):
        logging.info(f"开始获取 {code} 的数据")
        last = last_times.get(code)
        if last is None:
            last = begin
        get_price(code, last)
        logging.info(f"{code} 数据获取完成")
    logging.info("数据获取完成")
