import jieba

class Segmenter:
    def __init__(self, dict_path):
        """
        初始化分词类，加载自定义词典。
        
        :param dict_path: 自定义词典的路径
        """
        self.dict_path = dict_path
        jieba.load_userdict(self.dict_path)
    
    def segment(self, text):
        """
        分词方法，返回分词后的字符串。
        
        :param text: 要分词的文本
        :return: 分词后的字符串
        """
        words = jieba.lcut(text)
        return " ".join(words)

    
# 示例使用
if __name__ == "__main__":
    # 定义要分词的文本
    text = "威廉·萨默塞特·毛姆, CH，英国现代小说家、剧作家。他是那个时代最受欢迎的作家之一，据说是20世纪30年代收入最高的作家。 毛姆的父母在他10岁之前就去世了，他由一个情感淡漠的叔叔领养。他不想像家里的其他人一样成为一名律师，所以他接受了培训，取得了医生的资格。"

    # 创建分词器实例，并加载自定义词典
    segmenter = Segmenter("keyword_dict.txt")
    
    # 分词并打印结果
    segmented_text = segmenter.segment(text)
    print("分词结果: ", segmented_text)
