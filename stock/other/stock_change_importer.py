"""
-- 更新表结构：添加唯一索引，确保同一交易日/股票/变动人/变动股数/变动后股数唯一
ALTER TABLE daily_stock_change
  ADD UNIQUE KEY `daily_stock_change_trade_date_IDX` (`trade_date`,`stock_code`,`changer_name`,`change_shares`,`after_shares`) USING BTREE;
-- 确保 total_price 字段容量足够大
ALTER TABLE daily_stock_change
  MODIFY COLUMN total_price DECIMAL(18,2) NOT NULL COMMENT '总价';
"""
import random
import requests
from bs4 import BeautifulSoup
import pymysql
import logging
import time

# 配置日志
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

# AJAX URL 模板
URL_TEMPLATE = (
    "https://data.10jqka.com.cn/ajax/ggjy/field/enddate/order/desc/page/{page}/ajax/1/free/1/"
)

# 浏览器 Cookie
COOKIE_HEADER = 'v=A9graD0gBJ3bDSgZVRx-G6vBqQ1vwTxLniUQzxLJJJPGrXazutEM2-414F5h; Hm_lvt_60bad21af9c824a4a0530d5dbf4357ca=1747359654; Hm_lpvt_60bad21af9c824a4a0530d5dbf4357ca=1747359654; HMACCOUNT=2D5BC162F53EA96C; Hm_lvt_78c58f01938e4d85eaf619eae71b4ed1=1747359654; Hm_lpvt_78c58f01938e4d85eaf619eae71b4ed1=1747359654; Hm_lvt_f79b64788a4e377c608617fba4c736e2=1747359654; Hm_lpvt_f79b64788a4e377c608617fba4c736e2=1747359654'

# 初始化 Session
def create_session():
    session = requests.Session()
    headers = {
        'Host': 'data.10jqka.com.cn',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'sec-ch-ua': '"Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Referer': 'https://data.10jqka.com.cn/ggjy/',
        'Cookie': COOKIE_HEADER
    }
    session.headers.update(headers)
    # 预热：访问主页面抓取可能的动态 Cookie
    session.get('https://data.10jqka.com.cn')
    return session

# 解析增减持类型
def parse_change_type(text: str) -> str:
    return '减持' if text.startswith('-') else '增持'

# 规范化股数，支持 亿/万
def normalize_shares(text: str) -> float:
    if not text or text in ('', '--'):
        return 0.0
    t = text.replace(',', '').replace('-', '')
    try:
        if '亿' in t:
            return float(t.replace('亿', '')) * 1e8
        if '万' in t:
            return float(t.replace('万', '')) * 1e4
        return float(t)
    except ValueError:
        logging.warning(f"无法解析股数: {text}")
        return 0.0

# 抓取并解析单页数据
def fetch_page(session, page: int) -> list:
    url = URL_TEMPLATE.format(page=page)
    resp = session.get(url, headers={'X-Requested-With': 'XMLHttpRequest', 'Referer': url})
    resp.raise_for_status()
    html = resp.text
    if html.strip().startswith('{'):
        try:
            html = resp.json().get('data', '')
        except Exception:
            pass
    if not html:
        return []
    soup = BeautifulSoup(html, 'html.parser')
    rows = []
    for tr in soup.select('table.J-ajax-table tbody tr'):
        cols = tr.find_all('td')
        if len(cols) < 13:
            continue
        date = cols[4].get_text(strip=True)
        code = cols[1].get_text(strip=True)
        name = cols[2].get_text(strip=True)
        changer = cols[3].get_text(strip=True)
        raw = cols[5].get_text(strip=True)
        shares = normalize_shares(raw)
        price_txt = cols[6].get_text(strip=True)
        price = float(price_txt) if price_txt not in ('', '--') else 0.0
        total = round(shares * price, 2)
        after = normalize_shares(cols[9].get_text(strip=True))
        ratio = round(shares / (shares + after), 6) if (shares + after) > 0 else None
        reason = cols[7].get_text(strip=True)
        position = cols[12].get_text(strip=True)
        ctype = parse_change_type(raw)
        rows.append({
            'trade_date': date,
            'stock_code': code,
            'stock_name': name,
            'changer_name': changer,
            'changer_position': position,
            'change_type': ctype,
            'change_shares': shares,
            'price': price,
            'total_price': total,
            'after_shares': after,
            'change_ratio': ratio,
            'change_reason': reason
        })
    return rows


# 批量写入或更新
def insert_rows(rows: list):
    conn = pymysql.connect(**DB_CONFIG)
    cur = conn.cursor()
    sql = ("INSERT INTO daily_stock_change "
           "(trade_date,stock_code,stock_name,change_type,changer_name,changer_position,"  
           "change_shares,price,total_price,after_shares,change_ratio,change_reason) "
           "VALUES(%(trade_date)s,%(stock_code)s,%(stock_name)s,%(change_type)s,%(changer_name)s,"  
           "%(changer_position)s,%(change_shares)s,%(price)s,%(total_price)s,%(after_shares)s,"  
           "%(change_ratio)s,%(change_reason)s) "
           "ON DUPLICATE KEY UPDATE "
           "price=VALUES(price), total_price=VALUES(total_price), change_ratio=VALUES(change_ratio), "
           "change_reason=VALUES(change_reason), update_time=CURRENT_TIMESTAMP")
    cur.executemany(sql, rows)
    conn.commit()
    cur.close()
    conn.close()


def update_stock_base():
    conn = pymysql.connect(**DB_CONFIG)
    cur = conn.cursor()
    # 获取 stock_base 最晚 begin_time
    cur.execute("SELECT IFNULL(MAX(begin_time), '1970-01-01') FROM stock_base")
    max_time = cur.fetchone()[0]
    # 挑选后续未入库股票及其最早变动日期
    query = ("SELECT stock_code, stock_name, MIN(trade_date) AS begin_time "
             "FROM daily_stock_change "
             "WHERE trade_date > %s "
             "GROUP BY stock_code, stock_name")
    cur.execute(query, (max_time,))
    to_insert = cur.fetchall()
    # 批量插入忽略已存在
    insert_sql = ("INSERT IGNORE INTO stock_base "
                  "(stock_code, stock_name, begin_time) VALUES (%s, %s, %s)")
    cur.executemany(insert_sql, to_insert)
    conn.commit()
    cur.close()
    conn.close()


# 主流程
if __name__ == '__main__':
    session = create_session()
    max_pages = 12
    for page in range(1, max_pages + 1):
        logging.info(f"Fetching page {page}...")
        data_rows = fetch_page(session, page)
        if not data_rows:
            break
        insert_rows(data_rows)
        # 随机10-60秒的延迟
        wait_time = random.randint(10, 60)
        time.sleep(wait_time)
    # 更新基础股票表
    update_stock_base()
    logging.info('stock_base update completed.')