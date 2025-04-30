from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time

# 设置 ChromeDriver 的路径（根据你的 ChromeDriver 路径进行调整）
chrome_driver_path = 'D://PCTools//chromedriver-win64//chromedriver.exe'  # 替换为你的 ChromeDriver 路径

# 创建 ChromeDriver 服务对象
service = Service(executable_path=chrome_driver_path)

# 设置 ChromeOptions 来启用无头模式（可选）
chrome_options = Options()
chrome_options.add_argument('--headless')  # 启用 headless 模式
chrome_options.add_argument('--disable-gpu')  # 禁用 GPU 加速，避免部分问题

# 创建一个 Chrome 浏览器实例
driver = webdriver.Chrome(service=service, options=chrome_options)

# 打开指定的 URL
url = 'https://2b7kg8l3.ddwkx.cn/lobby/?uid=169825697&token=MTY5ODI1Njk3XzE3NDU5ODk2MDY1ODA6Y1pxYWl3aFJiRUoxbWNWQg&game=17&serverId=5171&wlang=zh-CN'
driver.get(url)
time.sleep(5)

# 截图初始页面
driver.save_screenshot("screenshot.png")

# 退出浏览器
driver.quit()
