import akshare as ak
import logging
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text  # 新增导入

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


# 创建SQLAlchemy引擎
def get_db_engine():
    conn_str = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}"
    return create_engine(conn_str)


# 获取数据库中最大 trade_date（修改SQL执行部分）
def get_latest_trade_date():
    engine = get_db_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT IFNULL(MAX(trade_date), '2000-01-01') FROM daily_stock_change"))
        latest_date = result.scalar()  # 直接获取标量结果
    return latest_date


# 获取并过滤 akshare 中文列数据（保持原逻辑不变）
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

    if isinstance(latest_date, str):
        latest_date = datetime.strptime(latest_date, "%Y-%m-%d").date()

    data["trade_date"] = pd.to_datetime(data["trade_date"]).dt.date
    data = data[data["trade_date"] >= latest_date]
    return data


# 判断增减持类型（保持原逻辑不变）
def parse_change_type(share: float) -> str:
    return "减持" if share < 0 else "增持"


# 规范化数据（保持原逻辑不变）
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


# 插入数据（保持原逻辑不变，仅修改连接方式）
def insert_rows(rows: list):
    if not rows:
        logging.info("No new rows to insert.")
        return

    logging.info(f"Inserting {len(rows)} records into database...")
    engine = get_db_engine()
    with engine.connect() as conn:
        insert_stmt = text("""
            INSERT INTO daily_stock_change (
                trade_date, stock_code, stock_name, change_type, changer_name, 
                changer_position, change_shares, price, total_price, after_shares, 
                change_ratio, change_reason
            )
            VALUES (
                :trade_date, :stock_code, :stock_name, :change_type, :changer_name, 
                :changer_position, :change_shares, :price, :total_price, :after_shares, 
                :change_ratio, :change_reason
            )
            ON DUPLICATE KEY UPDATE 
                price=VALUES(price), total_price=VALUES(total_price), 
                change_ratio=VALUES(change_ratio), change_reason=VALUES(change_reason),
                update_time=CURRENT_TIMESTAMP
        """)
        conn.execute(insert_stmt, rows)
        conn.commit()
    logging.info("Insert complete.")


# 更新 stock_base 表（修改SQL执行部分）
def update_stock_base():
    logging.info("Updating stock_base table...")
    engine = get_db_engine()

    # 获取最大时间
    with engine.connect() as conn:
        result = conn.execute(text("SELECT IFNULL(MAX(begin_time), '1970-01-01') FROM stock_base"))
        max_time = result.scalar()

    # 查询需要插入的数据
    with engine.connect() as conn:
        query = text("""
            SELECT stock_code, stock_name, MIN(trade_date) AS begin_time 
            FROM daily_stock_change 
            WHERE trade_date >= :max_time 
            GROUP BY stock_code, stock_name
        """)
        result = conn.execute(query, {"max_time": max_time})
        to_insert = result.fetchall()

    # 插入数据
    if to_insert:
        insert_stmt = text("""
            INSERT IGNORE INTO stock_base (stock_code, stock_name, begin_time) 
            VALUES (:stock_code, :stock_name, :begin_time)
        """)
        with engine.connect() as conn:
            conn.execute(insert_stmt, [dict(row._mapping) for row in to_insert])
            conn.commit()

    logging.info("stock_base update completed.")


# 主流程（保持原逻辑不变）
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
