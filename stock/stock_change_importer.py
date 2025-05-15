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

# AJAX URL template
URL_TEMPLATE = (
    "https://data.10jqka.com.cn/ajax/ggjy/field/enddate/order/desc/page/{page}/ajax/1/free/1/"
)

# Full Cookie header value copied from browser
COOKIE_HEADER = 'vvvv=1; v=A3mKC-SnNU1VKOnZnWbPyFKOiO5Whm04V3qRzJuu9aAfIpeQ49Z9COfKoZ0o'

# Initialize a session with all headers, including Cookie
def create_session():
    session = requests.Session()
    base_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'sdsfs /537.36 (KHTML, like Gecko) '
                      'EAFG/136.1.0.1 Safari/537.36 Edg/136.2.0.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,'
                  'image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cookie': COOKIE_HEADER
    }
    session.headers.update(base_headers)
    # Perform a GET to the AJAX URL to warm up session
    session.get(URL_TEMPLATE.format(page=1))
    return session

# Determine change type
def parse_change_type(share_text: str) -> str:
    return '减持' if share_text.startswith('-') else '增持'

# Convert shares text to number
def normalize_shares(text: str) -> float:
    if not text or text.strip() in ('', '--'):
        return 0.0
    num = text.replace('万', '').replace(',', '').replace('-', '')
    try:
        return float(num) * 10000
    except ValueError:
        return 0.0

# Fetch and parse one page
# Note: endpoint returns raw HTML fragment
def fetch_page(session: requests.Session, page: int) -> list:
    url = URL_TEMPLATE.format(page=page)
    resp = session.get(url)
    resp.raise_for_status()
    data_html = resp.text
    if data_html.strip().startswith('{'):
        try:
            data_html = resp.json().get('data', '')
        except Exception:
            pass
    if not data_html:
        print(f"Page {page}: Empty response")
        return []
    soup = BeautifulSoup(data_html, 'html.parser')
    rows = []
    for tr in soup.select('table.J-ajax-table tbody tr'):
        cols = tr.find_all('td')
        if len(cols) < 13:
            continue
        stock_code = cols[1].get_text(strip=True)
        stock_name = cols[2].get_text(strip=True)
        changer_name = cols[3].get_text(strip=True)
        trade_date = cols[4].get_text(strip=True)
        raw_shares = cols[5].get_text(strip=True)
        change_shares = normalize_shares(raw_shares)
        price_text = cols[6].get_text(strip=True)
        price = float(price_text) if price_text not in ('', '--') else 0.0
        # Compute total transaction amount
        total_price = round(change_shares * price, 2)
        change_reason = cols[7].get_text(strip=True)
        after_shares = normalize_shares(cols[9].get_text(strip=True))
        # Manual ratio calculation: change / (change + after)
        denom = change_shares + after_shares
        change_ratio = round(change_shares / denom, 6) if denom > 0 else None
        changer_position = cols[12].get_text(strip=True)
        change_type = parse_change_type(raw_shares)

        rows.append({
            'trade_date': trade_date,
            'stock_code': stock_code,
            'stock_name': stock_name,
            'change_type': change_type,
            'changer_name': changer_name,
            'changer_position': changer_position,
            'change_shares': change_shares,
            'price': price,
            'total_price': total_price,
            'after_shares': after_shares,
            'change_ratio': change_ratio,
            'change_reason': change_reason
        })
    return rows

# Bulk insert/update
def insert_rows(rows: list):
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    sql = ("INSERT INTO daily_stock_change "
           "(trade_date, stock_code, stock_name, change_type, changer_name, changer_position, "
           "change_shares, price, total_price, after_shares, change_ratio, change_reason) "
           "VALUES (%(trade_date)s, %(stock_code)s, %(stock_name)s, %(change_type)s, "
           "%(changer_name)s, %(changer_position)s, %(change_shares)s, %(price)s, %(total_price)s, "
           "%(after_shares)s, %(change_ratio)s, %(change_reason)s) "
           "ON DUPLICATE KEY UPDATE price=VALUES(price), total_price=VALUES(total_price), update_time=CURRENT_TIMESTAMP")
    try:
        cursor.executemany(sql, rows)
        conn.commit()
        print(f"Inserted/Updated {cursor.rowcount} records")
    except Exception as e:
        print(f"Error inserting rows: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

# Main execution
if __name__ == '__main__':
    session = create_session()
    max_pages = 12
    for page in range(1, max_pages + 1):
        print(f"Fetching page {page}...")
        data_rows = fetch_page(session, page)
        if not data_rows:
            break
        insert_rows(data_rows)
        # 随机10-60秒的延迟
        wait_time = random.randint(10, 60)
        time.sleep(wait_time)
