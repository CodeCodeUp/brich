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
url = 'http://10.10.200.172/dashboard'
driver.get(url)
time.sleep(5)

# 截图初始页面
driver.save_screenshot("screenshot.png")

# 输出账号密码
username = 'M088607'
password = '20250317a'
print(f"账号: {username}, 密码: {password}")

# 获取页面的大小（可以用来做坐标计算）
window_size = driver.get_window_size()
window_width = window_size['width']
window_height = window_size['height']

# 打印页面大小
print(f"页面宽度: {window_width}, 页面高度: {window_height}")

# 模拟点击屏幕上的某个坐标，假设我们点击屏幕的 (500, 450) 坐标
# 这个坐标应该是你想要点击的用户名输入框位置（根据页面布局调整）
x_offset = 500
y_offset = 450

# 使用 ActionChains 来移动到指定坐标并点击
actions = ActionChains(driver)
actions.move_by_offset(x_offset, y_offset).click().perform()

# 等待页面焦点更新
time.sleep(1)

actions.send_keys(Keys.TAB).perform()

# 输入账号
actions.send_keys(username).perform()

# 按下 Tab 键，跳转到密码输入框
actions.send_keys(Keys.TAB).perform()

# 输入密码
actions.send_keys(password).perform()

# 按回车键提交表单
actions.send_keys(Keys.RETURN).perform()

# 等待页面加载完成
time.sleep(3)

# 截图登录后的页面
driver.save_screenshot("screenshot2.png")

# 退出浏览器
driver.quit()
