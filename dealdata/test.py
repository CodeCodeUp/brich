import pandas as pd

from dealdata.get_data import get_data

# 假设 df 是你现有的 DataFrame
# 例如 df = pd.DataFrame({
#     'number_one': [1, 2, 3, 4, 5],
#     'number_two': [5, 4, 3, 2, 1]
# })

df = get_data()
# 将 number_one 列转化为 list
number_one_list = df['number_one'].tolist()

# 将列表写入到文件（例如一个 txt 文件）
file_path = 'number_one_output.txt'

with open(file_path, 'w') as f:
    f.write(','.join(map(str, number_one_list)))  # 用逗号分隔并写入文件


print(f"Data from 'number_one' column has been written to {file_path}")
