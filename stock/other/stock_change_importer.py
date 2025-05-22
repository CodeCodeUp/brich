import akshare as ak
import pymysql
import logging
import pandas as pd
from datetime import datetime

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='stock_change_import.log'
)

# 数据库配置
DB_CONFIG = {
    'host': '116.205.244.106',
    'user': 'root',
    'password': '202358hjq',
    'database': 'stock',
    'charset': 'utf8mb4'
}

# 获取数据库中最大 trade_date
def get_latest_trade_date():
    conn = pymysql.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT IFNULL(MAX(trade_date), '2000-01-01') FROM daily_stock_change")
    latest_date = cur.fetchone()[0]
    cur.close()
    conn.close()
    return latest_date

# 获取并过滤 akshare 中文列数据
def fetch_filtered_data(latest_date):
    logging.info("Fetching data from akshare...")
    data = ak.stock_hold_management_detail_em()
    data.rename(columns={
        "日期": "trade_date",
        "代码": "stock_code",
        "名称": "stock_name",
        "变动人": "changer_name",
        "职务": "changer_position",
        "变动股数": "change_shares",
        "成交均价": "price",
        "变动金额": "total_price",
        "变动后持股数": "after_shares",
        "变动比例": "change_ratio",
        "变动原因": "change_reason"
    }, inplace=True)

    # 修复：转成 datetime.date 类型
    if isinstance(latest_date, str):
        latest_date = datetime.strptime(latest_date, "%Y-%m-%d").date()

    data["trade_date"] = pd.to_datetime(data["trade_date"]).dt.date
    data = data[data["trade_date"] >= latest_date]
    return data

# 判断增减持类型
def parse_change_type(share: float) -> str:
    return "减持" if share < 0 else "增持"

# 规范化数据
def normalize_data(df):
    logging.info("Normalizing data...")
    df = df.copy()
    df["change_type"] = df["change_shares"].apply(parse_change_type)
    df["change_shares"] = df["change_shares"].abs()
    df["price"] = df["price"].fillna(0)
    df["total_price"] = df["total_price"].fillna(0)
    df["after_shares"] = df["after_shares"].fillna(0)
    df["change_ratio"] = df["change_ratio"].apply(lambda x: round(x / 100, 6) if pd.notna(x) else None)

    final_df = df[[
        "trade_date", "stock_code", "stock_name", "change_type",
        "changer_name", "changer_position", "change_shares", "price",
        "total_price", "after_shares", "change_ratio", "change_reason"
    ]]
    return final_df.to_dict(orient="records")

# 插入数据
def insert_rows(rows: list):
    if not rows:
        logging.info("No new rows to insert.")
        return

    logging.info(f"Inserting {len(rows)} records into database...")
    conn = pymysql.connect(**DB_CONFIG)
    cur = conn.cursor()

    sql = ("""
        INSERT INTO daily_stock_change (
            trade_date, stock_code, stock_name, change_type, changer_name, 
            changer_position, change_shares, price, total_price, after_shares, 
            change_ratio, change_reason
        )
        VALUES (
            %(trade_date)s, %(stock_code)s, %(stock_name)s, %(change_type)s, %(changer_name)s, 
            %(changer_position)s, %(change_shares)s, %(price)s, %(total_price)s, %(after_shares)s, 
            %(change_ratio)s, %(change_reason)s
        )
        ON DUPLICATE KEY UPDATE 
            price=VALUES(price), total_price=VALUES(total_price), 
            change_ratio=VALUES(change_ratio), change_reason=VALUES(change_reason),
            update_time=CURRENT_TIMESTAMP
    """)

    cur.executemany(sql, rows)
    conn.commit()
    cur.close()
    conn.close()
    logging.info("Insert complete.")

# 更新 stock_base 表
def update_stock_base():
    logging.info("Updating stock_base table...")
    conn = pymysql.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT IFNULL(MAX(begin_time), '1970-01-01') FROM stock_base")
    max_time = cur.fetchone()[0]

    query = ("SELECT stock_code, stock_name, MIN(trade_date) AS begin_time "
             "FROM daily_stock_change "
             "WHERE trade_date >= %s "
             "GROUP BY stock_code, stock_name")
    cur.execute(query, (max_time,))
    to_insert = cur.fetchall()

    insert_sql = ("INSERT IGNORE INTO stock_base "
                  "(stock_code, stock_name, begin_time) VALUES (%s, %s, %s)")
    cur.executemany(insert_sql, to_insert)
    conn.commit()
    cur.close()
    conn.close()
    logging.info("stock_base update completed.")

# 主流程
if __name__ == "__main__":
    try:
        logging.info("=== Daily Stock Change Script Started ===")
        latest_date = get_latest_trade_date()
        df = fetch_filtered_data(latest_date)
        if df.empty:
            logging.info("No new data from akshare.")
        else:
            records = normalize_data(df)
            insert_rows(records)
            update_stock_base()
        logging.info("=== Script Completed Successfully ===")
    except Exception as e:
        logging.exception("An error occurred during execution.")
