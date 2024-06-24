from datetime import datetime
import os
import shutil
import re

# 假设 caption 是一个包含文本的对象
caption = type('', (), {})()  # 创建一个空对象模拟caption
caption.text = "这是一个包含汉字的文本 example text"

def contains_chinese(text):
    """检查字符串中是否包含汉字"""
    hanzi_pattern = re.compile(r'[\u4e00-\u9fff]')
    return hanzi_pattern.search(text) is not None



def get_filename_without_extension(path_or_filename):
    # 使用 os.path.basename 获取路径中的文件名（带后缀）
    filename_with_extension = os.path.basename(path_or_filename)
    
    # 使用 os.path.splitext 分割文件名和后缀
    filename, file_extension = os.path.splitext(filename_with_extension)
    
    # 返回不带后缀的文件名部分
    return filename


class FileOrganizer:
    def __init__(self, root_folder):
        self.root_folder = root_folder

    def process_subfolders(self, operation_func):
        """
        递归遍历根文件夹及其所有子文件夹，并对每个文件应用指定的操作函数。
        
        Args:
            operation_func (function): 要应用于文件的操作函数，该函数应接收文件的绝对路径作为参数。
        """
        for root, dirs, files in os.walk(self.root_folder):
            for file in files:
                file_path = os.path.join(root, file)
                operation_func(file_path)


    # 操作文件夹下的所有子文件夹指定后缀的内容
    def process_subdirectories_specify_suffix_file(self, handle, suffix):
        # 列出当前目录下的所有文件和文件夹
        for entry in os.listdir(self.root_folder):
            # 构建完整的路径
            entry_path = os.path.join(self.root_folder, entry)
            # 如果是文件夹，则递归处理子文件夹
            if os.path.isdir(entry_path):
                file = os.path.join(entry_path,entry+"."+suffix)
                if os.path.exists(file):
                    handle(file)  # 递归调用处理子文件夹
                else:
                    handle(None)


    # 操作文件夹下的所有子文件夹指定后缀的内容
    def process_subdirectories(self, handle):
        # 列出当前目录下的所有文件和文件夹
        for entry in os.listdir(self.root_folder):
            # 构建完整的路径
            entry_path = os.path.join(self.root_folder, entry)
            # 如果是文件夹，则递归处理子文件夹
            if os.path.isdir(entry_path):
                handle(entry_path)  # 递归调用处理子文件夹
                # try:
                # except Exception as e:
                #     print(e)

                    
    # 归类：创建同名的子文件夹 并且按照相同的名字归类
    def organize_files(self):
        # 获取指定文件夹下所有文件的绝对路径
        file_paths = [os.path.abspath(os.path.join(self.root_folder, filename)) 
                      for filename in os.listdir(self.root_folder)
                      if os.path.isfile(os.path.join(self.root_folder, filename))]
        
        # 使用字典来按文件名分组
        file_dict = {}
        for file_path in file_paths:
            filename, extension = os.path.splitext(os.path.basename(file_path))
            if filename not in file_dict:
                file_dict[filename] = []
            file_dict[filename].append((file_path, extension))
        
        # 遍历分组，创建子文件夹并移动文件
        for filename, files in file_dict.items():
            folder_path = os.path.join(self.root_folder, filename)
            os.makedirs(folder_path, exist_ok=True)  # 创建子文件夹
            
            for file_path, extension in files:
                new_file_path = os.path.join(folder_path, f"{filename}{extension}")
                shutil.move(file_path, new_file_path)  # 移动文件到子文件夹


    def get_lowercase_extension(self, filename):
        """返回文件的小写后缀"""
        _, extension = os.path.splitext(filename)
        return extension.lower()


def read_txt_file(file_path):
    try:
        # 打开文件并读取内容，使用 utf-8 编码
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content  # 返回读取的文件内容

    except FileNotFoundError:
        print(f"文件 '{file_path}' 不存在")
    except Exception as e:
        print(f"读取文件 '{file_path}' 发生错误：{e}")
    
    return None  # 发生异常时返回 None


def last_folder_name(abs_path):
    # 使用 os.path.split() 函数来分割路径，得到 (head, tail) 的形式
    head, tail = os.path.split(abs_path)
    
    # 如果 tail 不为空，说明 abs_path 是文件夹路径，直接返回 tail
    if tail:
        return tail
    
    # 否则继续分割 head，直到找到最后一个非空的文件夹名
    while head:
        head, tail = os.path.split(head)
        if tail:
            return tail
    
    # 如果路径为空或者没有文件夹名，则返回空字符串
    return ''


def find_file_with_extension(root_dir, target_extension):
    # 遍历指定目录及其子目录下的所有文件和文件夹
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            # 获取文件的绝对路径
            file_path = os.path.join(root, file)
            # 检查文件是否以指定后缀结尾
            if file_path.endswith(target_extension):
                return os.path.normpath(file_path)  # 返回找到的文件的绝对路径

    # 如果未找到指定后缀的文件，返回None
    return None

def time_str_to_timestamp(time_str):
    # 解析时间字符串
    dt = datetime.strptime(time_str, "%H:%M:%S.%f")
    # 将时间转换为时间戳（以秒为单位的浮点数）
    timestamp = dt.hour * 3600 + dt.minute * 60 + dt.second + dt.microsecond / 1e6
    return timestamp
