import time
import logging
from datetime import datetime, timedelta
import pandas as pd
import akshare as ak
import pymysql

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

# 获取需跟踪的股票及其起始时间
def fetch_stock_list():
    conn = pymysql.connect(**DB_CONFIG)
    df = pd.read_sql("SELECT stock_code, begin_time FROM stock_base", conn)
    conn.close()
    df['stock_code'] = df['stock_code'].astype(str)
    df['begin_time'] = pd.to_datetime(df['begin_time'])
    return df

def fetch_last_times(codes):
    conn = pymysql.connect(**DB_CONFIG)
    sql = ("SELECT stock_code, MAX(track_time) AS last_time "
           "FROM stock_price_tracking "
           "WHERE stock_code IN ({}) "
           "GROUP BY stock_code").format(','.join(['%s']*len(codes)))
    cur = conn.cursor()
    cur.execute(sql, codes)
    rows = cur.fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}


# 插入行情数据，支持 DataFrame 或 dict 格式的 quote
def insert_quote(code, quote):
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
        # 只保留时间是30分或者整点的记录
        current_time = pd.Timestamp(row[0])  # 或者直接使用 row[0]，取决于数据类型
        if current_time.minute not in [0, 30]:
            continue
        try:
            cur.execute(sql, (
                code,
                row[0],
                row[7],
                row[1],
                row[2],
                row[3],
                row[4],
                row[5],
                None if row[7] == 0 else (row[4] - row[7]) / row[7] * 100
            ))
        except Exception as e:
            logging.error(f"{code} 插入数据异常: {e}")
        finally:
            conn.commit()
    cur.close()


def get_price(code, begin):
    quote = None
    try:
        quote = ak.stock_zh_a_hist_min_em(symbol=code, period="1", adjust="qfq", start_date=begin)
        if quote is None or len(quote) == 0:
            logging.error(f"{code} 获取数据失败")
            return
        insert_quote(code, quote)
    except Exception as e:
        logging.error(f"{code} 获取数据异常: {e}, 数据: {quote}")


if __name__ == '__main__':
    while True:
        now = datetime.now().replace(second=0, microsecond=0)
        stock_df = fetch_stock_list()
        codes = stock_df['stock_code'].tolist()
        last_times = fetch_last_times(codes)
        for code, begin in stock_df.itertuples(index=False):
            last = last_times.get(code)
            if last is None:
                last = begin
            get_price(code, last)
        time.sleep(1800)
