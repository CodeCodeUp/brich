# 统计每个数字的概率
import pandas as pd


class ProbabilityCalculator:
    def __init__(self, df, columns):
        """
        初始化概率计算类

        :param df: 输入的 DataFrame，包含每列数据
        :param columns: 要计算概率的列名列表
        """
        self.df = df
        self.columns = columns

    def calculate_probability(self):
        """
        计算每列每个数字的出现概率

        :return: 返回一个 DataFrame，其中包含每个数字的出现次数和概率
        """
        probability_results = {}

        # 遍历每一列
        for col in self.columns:
            # 创建一个字典来存储每个数字的出现次数
            count_dict = {str(i): 0 for i in range(10)}  # 数字0到9的计数

            # 统计每个数字的出现次数
            for value in self.df[col]:
                if str(value).isdigit():  # 确保是数字
                    count_dict[str(value)] += 1

            # 计算每个数字的概率
            total_rows = len(self.df)
            probability_dict = {k: v / total_rows for k, v in count_dict.items()}

            # 存储结果
            probability_results[col] = {
                'counts': count_dict,
                'probabilities': probability_dict
            }

        # 将结果转化为DataFrame，方便查看
        counts_df = pd.DataFrame({col: results['counts'] for col, results in probability_results.items()})
        probabilities_df = pd.DataFrame({col: results['probabilities'] for col, results in probability_results.items()})

        # 返回包含次数和概率的DataFrame
        return counts_df, probabilities_df

    def print_probability(self):
        """
        打印每列每个数字的出现次数和概率
        """
        counts_df, probabilities_df = self.calculate_probability()

        print("每列数字出现次数：")
        print(counts_df)
        print("\n每列数字出现概率：")
        print(probabilities_df)
