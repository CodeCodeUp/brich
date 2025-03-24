import requests
import time
import smtplib
import yaml
import logging
from email.mime.text import MIMEText
from datetime import datetime
from sqlalchemy import create_engine, text


def is_big_for_position(url_type, position, number):
    """根据位置和类型判断是否为大数"""
    # 处理-1的特殊情况
    if number == -1:
        return None  # 既不统计大也不统计小

    # 类型6/7的第四个位置的特殊逻辑
    if str(url_type) in ['6', '7'] and position == 4:
        if 10 < number <= 17:
            return True
        elif 4 <= number <= 10:  # 明确区间划分，避免10的歧义
            return False
        else:
            return None  # 超出预期范围的值不参与统计
    if str(url_type) in ['6', '7'] and position != 4:
        return None  # 超出预期范围的值不参与统计

    # 其他情况保持原有逻辑（>=5为大）
    return number >= 5


def is_silent_time():
    """判断当前是否处于静默时段（23:00-07:30）"""
    current_time = datetime.now().time()
    silent_start = datetime.strptime("23:00", "%H:%M").time()
    silent_end = datetime.strptime("07:30", "%H:%M").time()
    return current_time >= silent_start or current_time <= silent_end


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

    def send_email(self, content):
        """发送报警邮件"""
        # 检查邮件功能是否启用
        if not self.email_config["enabled"]:
            logging.info(f"[邮件通知已禁用] {content}")
            return

        # 检查静默时段
        if is_silent_time():
            logging.info(f"[静默时段] 已跳过邮件发送: {content}")
            return

        # 构造邮件内容
        msg = MIMEText(content)
        msg['Subject'] = content
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
                        # 原始数据转换
                        raw_numbers = [int(num) for num in draw["drawResult"]]

                        # 特殊处理类型6/7
                        if str(url_type) in ['6', '7']:
                            if len(raw_numbers) < 3:
                                logging.error(f"数据错误: {url_type}类型需要至少3个数字，但只获取到{len(raw_numbers)}个")
                                continue
                            num1, num2, num3 = raw_numbers[:3]
                            num4 = -1 if num1 == num2 == num3 else (num1 + num2 + num3)
                            processed_numbers = [num1, num2, num3, num4, None]  # number5为None
                        else:
                            processed_numbers = raw_numbers[:5]  # 正常取前5个
                            if len(processed_numbers) < 5:
                                logging.error(
                                    f"数据错误: {url_type}类型需要5个数字，但只获取到{len(processed_numbers)}个")
                                continue

                        # 插入数据库
                        self.insert_into_db(url_type, draw_number, processed_numbers)
                        # 更新统计和报警（使用处理后的完整数据）
                        self.update_counts_and_alert(url_type, processed_numbers)
            except Exception as e:
                logging.error(f"处理 {url} 时出错: {e}")

    def insert_into_db(self, url_type, draw_number, draw_result):
        """插入数据到数据库"""
        insert_time = datetime.now()

        # 根据url_type处理数据
        if str(url_type) in ['6', '7']:  # 确保类型判断为字符串
            # 只处理前三个数字
            if len(draw_result) < 3:
                logging.error(f"数据错误: {url_type}类型需要至少3个数字，但只获取到{len(draw_result)}个")
                return

            num1 = draw_result[0]
            num2 = draw_result[1]
            num3 = draw_result[2]

            # 计算number4
            if num1 == num2 == num3:
                num4 = -1
            else:
                num4 = num1 + num2 + num3

            # number5留空，设为None
            num5 = None
        else:
            # 正常处理五个数字
            if len(draw_result) < 5:
                logging.error(f"数据错误: {url_type}类型需要5个数字，但只获取到{len(draw_result)}个")
                return
            num1, num2, num3, num4, num5 = draw_result[:5]

        # 构造插入参数
        params = {
            "nid": draw_number,
            "number_one": num1,
            "number_two": num2,
            "number_three": num3,
            "number_four": num4,
            "number_five": num5,
            "type": url_type,
            "insert_time": insert_time
        }

        # 执行插入
        insert_query = text("""
            INSERT INTO base_data (nid, number_one, number_two, number_three, 
            number_four, number_five, type, insert_time)
            VALUES (:nid, :number_one, :number_two, :number_three, 
            :number_four, :number_five, :type, :insert_time)
        """)
        try:
            with self.engine.connect() as connection:
                connection.execute(insert_query, params)
                connection.commit()
            logging.info(f"数据入库成功 类型:{url_type} 期号:{draw_number}")
        except Exception as e:
            logging.error(f"数据入库失败 类型:{url_type} 期号:{draw_number}: {e}")

    def update_counts_and_alert(self, url_type, processed_numbers):
        """更新大小计数，并发送警报（处理特殊逻辑）"""
        for pos, num in enumerate(processed_numbers, start=1):
            # 获取当前数字的实际位置（1-5）
            current_pos = pos

            # 跳过空值
            if num is None:
                continue

            # 获取大小判断结果
            is_big = is_big_for_position(url_type, current_pos, num)

            # 处理-1和无效值
            if is_big is None:
                self.consecutive_counts[url_type][current_pos]["big"] = 0
                self.consecutive_counts[url_type][current_pos]["small"] = 0
                continue

            # 更新计数器
            if is_big:
                self.consecutive_counts[url_type][current_pos]["big"] += 1
                self.consecutive_counts[url_type][current_pos]["small"] = 0
                threshold = self.threshold_config[url_type][current_pos]["big"]
            else:
                self.consecutive_counts[url_type][current_pos]["small"] += 1
                self.consecutive_counts[url_type][current_pos]["big"] = 0
                threshold = self.threshold_config[url_type][current_pos]["small"]

            # 触发报警逻辑
            if (is_big and self.consecutive_counts[url_type][current_pos]["big"] > threshold) or \
                    (not is_big and self.consecutive_counts[url_type][current_pos]["small"] > threshold):
                alert_type = "B" if is_big else "S"
                count = self.consecutive_counts[url_type][current_pos]["big" if is_big else "small"]
                alert_msg = f"{url_type}--{current_pos} --{alert_type}-- {count}"
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