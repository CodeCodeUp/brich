import requests
import time
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from sqlalchemy import create_engine, text


class LotteryMonitor:
    def __init__(self, url_config, threshold_config, email_config, db_url):
        """
        :param url_config: dict，每个 key 代表一种类型（对应一个 URL），value 为数据接口 URL
        :param threshold_config: dict，结构为 {类型: {位置: {"big": 阈值, "small": 阈值}}}，
                                 如 {1: {1: {"big": 7, "small": 8}, 2: {...}, ...}, 2: {...}, ...}
        :param email_config: dict，包含发件人、SMTP服务器、端口、密码、接收人等信息
        :param db_url: 数据库连接字符串，例如 'mysql+pymysql://root:123456@127.0.0.1:3306/brich'
        """
        self.url_config = url_config
        self.threshold_config = threshold_config
        self.email_config = email_config
        self.engine = create_engine(db_url)
        self.session = requests.Session()
        self.session.cookies.set('visitor_id', 'bef8e599-0bc7-4305-8dfa-228b1eb71ed5')
        # 用于统计连续“大”“小”的次数，仅更新新入库的数据
        # 结构：{类型: {位置: {"big": count, "small": count}}}
        self.consecutive_counts = {
            url_type: {pos: {"big": 0, "small": 0} for pos in range(1, 6)}
            for url_type in self.url_config.keys()
        }

    def send_email(self, content):
        """发送报警邮件，内容格式为 '类型X 位置Y 连续大/小 Z 次'"""
        msg = MIMEText(content)
        msg['Subject'] = 'Lottery Alert'
        msg['From'] = self.email_config["sender"]
        msg['To'] = self.email_config["receiver"]

        try:
            smtp = smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"])
            smtp.starttls()
            smtp.login(self.email_config["sender"], self.email_config["password"])
            smtp.send_message(msg)
            smtp.quit()
            print(f"{datetime.now()} 发送提醒成功: {content}")
        except Exception as e:
            print(f"{datetime.now()} 发送邮件失败: {e}")

    def is_big(self, number):
        """判断数字是否为 '大'（定义：>= 5 为大，< 5 为小，可根据需要调整）"""
        return number >= 5

    def insert_into_db(self, url_type, draw):
        """
        入库一条新数据（仅入库 drawNumber 大于数据库中该类型最大 nid 的数据）
        :param url_type: 当前数据所属的类型（对应 url_config 的 key）
        :param draw: dict，包含 drawNumber 和 drawResult（列表，依次对应 number_one~number_five）
        """
        try:
            draw_number = int(draw["drawNumber"].replace("-", ""))
        except Exception as e:
            print(f"{datetime.now()} 解析 drawNumber 入库失败: {e}")
            return

        try:
            draw_result = [int(num) for num in draw["drawResult"]]
        except Exception as e:
            print(f"{datetime.now()} 解析 drawResult 入库失败: {e}")
            return

        insert_time = datetime.now()
        insert_query = text("""
            INSERT INTO base_data (nid, number_one, number_two, number_three, number_four, number_five, type, insert_time)
            VALUES (:nid, :number_one, :number_two, :number_three, :number_four, :number_five, :type, :insert_time)
        """)
        try:
            with self.engine.connect() as connection:
                connection.execute(insert_query, {
                    "nid": draw_number,
                    "number_one": draw_result[0],
                    "number_two": draw_result[1],
                    "number_three": draw_result[2],
                    "number_four": draw_result[3],
                    "number_five": draw_result[4],
                    "type": url_type,
                    "insert_time": insert_time
                })
                connection.commit()
                print(f"{datetime.now()} 类型 {url_type} 数据 {draw_number} 入库成功")
        except Exception as e:
            print(f"{datetime.now()} 入库时出错（类型 {url_type} draw {draw_number}）：{e}")

    def update_counts_and_alert(self, url_type, draw):
        """
        根据入库的新数据更新连续“大”“小”计数，并判断是否需要报警
        :param url_type: 当前数据所属类型
        :param draw: dict，包含 drawResult（列表，对应 5 个号码）
        """
        for pos, num_val in enumerate(draw["drawResult"], start=1):
            try:
                num = int(num_val)
            except Exception as e:
                print(f"{datetime.now()} 解析 drawResult 数字失败: {e}")
                continue

            if self.is_big(num):
                self.consecutive_counts[url_type][pos]["big"] += 1
                self.consecutive_counts[url_type][pos]["small"] = 0  # 重置小计数
                current_count = self.consecutive_counts[url_type][pos]["big"]
                threshold = self.threshold_config[url_type][pos]["big"]
                if current_count > threshold:
                    content = f"{url_type} -{pos} - {current_count} "
                    self.send_email(content)
            else:
                self.consecutive_counts[url_type][pos]["small"] += 1
                self.consecutive_counts[url_type][pos]["big"] = 0  # 重置大计数
                current_count = self.consecutive_counts[url_type][pos]["small"]
                threshold = self.threshold_config[url_type][pos]["small"]
                if current_count > threshold:
                    content = f"{url_type} -{pos} - {current_count} "
                    self.send_email(content)

    def process_new_data(self):
        """
        对于每个类型（即每个 URL）：
         1. 先查询数据库中该类型的最大 nid；
         2. 请求 URL 获取数据，并按 drawNumber 升序排序；
         3. 对于 drawNumber 大于数据库最大值的新数据，依次入库，同时更新连续统计（仅用新入库的数据判断）。
        """
        for url_type, url in self.url_config.items():
            # 从数据库中获取该类型的最大 nid
            try:
                with self.engine.connect() as connection:
                    select_max_query = text("SELECT MAX(nid) FROM base_data WHERE type = :url_type")
                    result = connection.execute(select_max_query, {"url_type": url_type})
                    max_db_row = result.fetchone()
                    max_db_nid = int(max_db_row[0]) if max_db_row[0] is not None else 0
            except Exception as e:
                print(f"{datetime.now()} 查询类型 {url_type} 最大 nid 出错: {e}")
                continue

            try:
                response = self.session.get(url, timeout=10)
                data = response.json()
                draw_results = data.get("drawResults", [])
                if not draw_results:
                    continue

                # 按 drawNumber 升序排序，确保按时间顺序处理
                draw_results_sorted = sorted(draw_results, key=lambda d: int(d["drawNumber"].replace("-", "")))
                for draw in draw_results_sorted:
                    try:
                        draw_number = int(draw["drawNumber"].replace("-", ""))
                    except Exception as e:
                        print(f"{datetime.now()} 解析 drawNumber 出错: {e}")
                        continue

                    # 只处理大于数据库中最大 nid 的数据
                    if draw_number > max_db_nid:
                        self.insert_into_db(url_type, draw)
                        self.update_counts_and_alert(url_type, draw)
            except Exception as e:
                print(f"{datetime.now()} 请求或解析 {url} 出现错误: {e}")


def main():
    # 每个 URL 对应一种类型，每种类型有 5 个号码需要统计
    url_config = {
        1: 'https://www.ub8.com/ajax/draw/TWBSSC/result?numOfDraw=3000',
        2: 'https://www.ub8.com/ajax/draw/ASHAREF2SSC/result?numOfDraw=3000',
        3: 'https://www.ub8.com/ajax/draw/APF10SSC/result?numOfDraw=3000',
        4: 'https://www.ub8.com/ajax/draw/BAF5SSC/result?numOfDraw=3000',
        5: 'https://www.ub8.com/ajax/draw/BAF3SSC/result?numOfDraw=3000'
    }
    # 各类型各位置报警阈值配置（可按需调整）
    threshold_config = {
        1: {1: {"big": 7, "small": 8},
            2: {"big": 7, "small": 8},
            3: {"big": 7, "small": 8},
            4: {"big": 7, "small": 8},
            5: {"big": 7, "small": 8}},
        2: {1: {"big": 6, "small": 2},
            2: {"big": 6, "small": 2},
            3: {"big": 6, "small": 4},
            4: {"big": 6, "small": 4},
            5: {"big": 6, "small": 4}},
        3: {1: {"big": 8, "small": 8},
            2: {"big": 8, "small": 8},
            3: {"big": 8, "small": 8},
            4: {"big": 8, "small": 8},
            5: {"big": 8, "small": 8}},
        4: {1: {"big": 8, "small": 8},
            2: {"big": 8, "small": 8},
            3: {"big": 8, "small": 8},
            4: {"big": 8, "small": 8},
            5: {"big": 8, "small": 8}},
        5: {1: {"big": 8, "small": 8},
            2: {"big": 8, "small": 8},
            3: {"big": 8, "small": 8},
            4: {"big": 8, "small": 8},
            5: {"big": 8, "small": 8}},
    }
    # 邮件配置信息，请替换为你自己的信息
    email_config = {
        "sender": "1985238626@qq.com",  # 发件邮箱
        "password": "csykporsppagbffa",  # 发件邮箱密码
        "smtp_server": "smtp.qq.com",  # SMTP 服务器
        "smtp_port": 587,  # SMTP 端口
        "receiver": "1985238626@qq.com"  # 接收提醒的邮箱
    }
    # 数据库连接字符串
    db_url = 'mysql+pymysql://root:123456@127.0.0.1:3306/brich'

    monitor = LotteryMonitor(url_config, threshold_config, email_config, db_url)

    while True:
        monitor.process_new_data()
        # 每 60 秒检查一次新数据
        time.sleep(60)


if __name__ == '__main__':
    main()
