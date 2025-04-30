from paddleocr import PaddleOCR

# 初始化 PaddleOCR，禁用文本检测
ocr = PaddleOCR()
# 读取图像
img_path = 'D://1.png'  # 请替换为您的图片路径
result = ocr.ocr(img_path, det=False, cls=True)  # 关键参数 det=False
print(result)

for line in result:
    print(f"识别的文本: {line[0]}")