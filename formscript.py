import os
from pymongo import MongoClient

# 连接 MongoDB
client = MongoClient('mongodb://localhost:27017/')
# 创建或选择数据库
db = client['script']
# 选择集合
collection = db['scripts_collection']

# 文件夹路径
folder_path = 'E:/bysj/scirpt-backend/jubenPro'

# 遍历文件夹
for filename in os.listdir(folder_path):
    if filename.endswith('.txt'):
        with open(os.path.join(folder_path, filename), 'r', encoding='utf-8') as file:
            # 读取剧本内容
            script_content = file.read()
            # 创建要插入的文档
            script_doc = {
                'title': filename[:-4],  # 剔除文件扩展名作为标题
                'content': script_content
            }
            # 插入文档到 MongoDB
            collection.insert_one(script_doc)

print("剧本导入完成！")
