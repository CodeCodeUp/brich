import requests
import time
import smtplib
import yaml
import logging
from email.mime.text import MIMEText
from datetime import datetime
from sqlalchemy import create_engine, text


class LotteryMonitor:
    def __init__(self, config_path):
        # 读取配置文件
        with open(config_path, "r", encoding="utf-8") as file:
            self.config = yaml.safe_load(file)

        self.url_config = self.config["urls"]
        self.threshold_config = self.config["thresholds"]
        self.email_config = self.config["email"]
        self.engine = create_engine(self.config["database"]["url"])
        self.session = requests.Session()
        self.session.cookies.set('visitor_id', 'bef8e599-0bc7-4305-8dfa-228b1eb71ed5')

        # 统计每个位置的连续大/小次数
        self.consecutive_counts = {
            url_type: {pos: {"big": 0, "small": 0} for pos in range(1, 6)}
            for url_type in self.url_config.keys()
        }

    def is_silent_time(self):
        """判断当前是否处于静默时段（23:00-07:30）"""
        current_time = datetime.now().time()
        silent_start = datetime.strptime("23:00", "%H:%M").time()
        silent_end = datetime.strptime("07:30", "%H:%M").time()
        return current_time >= silent_start or current_time <= silent_end

    def send_email(self, content):
        """发送报警邮件"""
        # 检查邮件功能是否启用
        if not self.email_config["enabled"]:
            logging.info(f"[邮件通知已禁用] {content}")
            return

        # 检查静默时段
        if self.is_silent_time():
            logging.info(f"[静默时段] 已跳过邮件发送: {content}")
            return

        # 构造邮件内容
        msg = MIMEText(content)
        msg['Subject'] = 'Lottery Alert'
        msg['From'] = self.email_config["sender"]
        msg['To'] = self.email_config["receiver"]

        try:
            # 发送邮件
            with smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"]) as smtp:
                smtp.starttls()
                smtp.login(self.email_config["sender"], self.email_config["password"])
                smtp.send_message(msg)
            logging.info(f"邮件发送成功: {content}")
        except Exception as e:
            logging.error(f"邮件发送失败: {e}")

    def is_big(self, number):
        """判断是否为 '大'（>= 5 为大）"""
        return number >= 5

    def process_new_data(self):
        """处理新数据"""
        for url_type, url in self.url_config.items():
            try:
                with self.engine.connect() as connection:
                    select_max_query = text("SELECT MAX(nid) FROM base_data WHERE type = :url_type")
                    result = connection.execute(select_max_query, {"url_type": url_type})
                    max_db_nid = int(result.fetchone()[0] or 0)

                response = self.session.get(url, timeout=10)
                draw_results = response.json().get("drawResults", [])
                draw_results_sorted = sorted(draw_results, key=lambda d: int(d["drawNumber"].replace("-", "")))

                for draw in draw_results_sorted:
                    draw_number = int(draw["drawNumber"].replace("-", ""))
                    if draw_number > max_db_nid:
                        draw_result = [int(num) for num in draw["drawResult"]]
                        self.insert_into_db(url_type, draw_number, draw_result)
                        self.update_counts_and_alert(url_type, draw_result)
            except Exception as e:
                logging.error(f"处理 {url} 时出错: {e}")

    def insert_into_db(self, url_type, draw_number, draw_result):
        """插入数据到数据库"""
        insert_time = datetime.now()
        insert_query = text("""
            INSERT INTO base_data (nid, number_one, number_two, number_three, 
            number_four, number_five, type, insert_time)
            VALUES (:nid, :number_one, :number_two, :number_three, 
            :number_four, :number_five, :type, :insert_time)
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
            logging.info(f"数据入库成功 类型:{url_type} 期号:{draw_number}")
        except Exception as e:
            logging.error(f"数据入库失败 类型:{url_type} 期号:{draw_number}: {e}")

    def update_counts_and_alert(self, url_type, draw_result):
        """更新大小计数，并发送警报"""
        for pos, num in enumerate(draw_result, start=1):
            if self.is_big(num):
                self.consecutive_counts[url_type][pos]["big"] += 1
                self.consecutive_counts[url_type][pos]["small"] = 0
                if self.consecutive_counts[url_type][pos]["big"] > self.threshold_config[url_type][pos]["big"]:
                    alert_msg = f"{url_type}--{pos} --B-- {self.consecutive_counts[url_type][pos]['big']}"
                    self.send_email(alert_msg)
            else:
                self.consecutive_counts[url_type][pos]["small"] += 1
                self.consecutive_counts[url_type][pos]["big"] = 0
                if self.consecutive_counts[url_type][pos]["small"] > self.threshold_config[url_type][pos]["small"]:
                    alert_msg = f"{url_type}--{pos} --S-- {self.consecutive_counts[url_type][pos]['small']}"
                    self.send_email(alert_msg)


def main():
    # 配置日志系统
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("lottery_monitor.log"),
            logging.StreamHandler()
        ]
    )

    monitor = LotteryMonitor("config.yaml")

    while True:
        try:
            monitor.process_new_data()
            time.sleep(30)
        except KeyboardInterrupt:
            logging.info("用户中断服务")
            break
        except Exception as e:
            logging.error(f"主循环发生错误: {e}")
            time.sleep(60)


if __name__ == '__main__':
    main()