import datetime
import os
import re
from flask import Flask, jsonify, request
from flask_cors import CORS
from models import User  # 导入 User 模型
from extensions import db
from pymongo import MongoClient
from bson import ObjectId,json_util
from handle_script import Script



app = Flask(__name__)
CORS(app)

# 配置数据库连接
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost/vboxuser'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = './script'
db.init_app(app)

connect = MongoClient('mongodb://127.0.0.1:27017')
my_db = connect["script"]
collection = my_db['scripts'] 

filmcollection=my_db['scripts_collection']

promptcollection=my_db['prompt']

@app.route('/get_prompt',methods=['POST'])
def get_prompt():
    prompts = list(promptcollection.find({}, {'_id': 0}))  # Retrieve all documents from the promptcollection
    return json_util.dumps({"prompts":prompts})

@app.route('/process_script', methods=['POST'])
def process_script():
    # 解析接收到的 JSON 数据
    script_data = request.json
    script_name = script_data.get('script_name')
    script_text = script_data.get('script_text')

    # 将剧本文本保存到文件中
    script_filename = save_script_to_file(script_name, script_text)

    # 处理剧本
    result = process_script_file(script_filename)

    return jsonify(result)

def save_script_to_file(script_name, script_text):
    save_path = "scripts/"
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    script_filename = os.path.join(save_path, script_name + ".txt")
    with open(script_filename, 'w', encoding='utf-8') as file:
        file.write(script_text)
    return script_filename

def process_script_file(script_filename):
    script = Script(script_filename)
    script.cal_all_info()
    script_roles = ""
    for role_name, word_count in script.charactor_overrall_word_count_dic.items():
            # print(role_name,self.charactor_overral_apear_in_session[role_name],word_count)
        script_roles += role_name + '\t' + str(word_count) + '\t' + str(
        script.charactor_overral_apear_in_session[role_name]) + '\n'
    session_information=script.write_script_detail()
    emotion_participle=script.write_participle()
    session_role_word=script.write_session_role_word()
    session_ad_args=script.write_session_ad_args()
    script_sensitive_args=script.wrtie_script_sensitive_args()
    # 构建回复结果
    result = {
        "success": True,
        "message": "剧本处理完毕",
        # 你可以根据需要自定义回复的内容
        # 比如返回处理后的文件路径或者其他信息
        "charcter":script_roles,    #角色信息
        "session_information":session_information, #场景信息
        "emotion_participle":emotion_participle,    #情感分词
        "session_role_word":session_role_word,   #角色情感词频
        "session_ad_args":session_ad_args, #广告词频率
        "script_sensitive_args":script_sensitive_args #敏感词频

    }
    return result


@app.route('/getscriptcontent', methods=['POST'])
def get_script_content():
    # 检查请求中是否包含 JSON 数据
    if not request.is_json:
        return jsonify({'success': False, 'message': '请求数据不是 JSON 格式'}), 400

    # 获取 JSON 数据
    data = request.json

    # 从 JSON 数据中提取所需字段
    script_id = data.get('_id')

    try:
        # 尝试将 script_id 转换为 ObjectId
        script_id = ObjectId(script_id)
    except Exception as e:
        return jsonify({'success': False, 'message': '无效的剧本 ID'}), 400

    # 在 MongoDB 中查找对应的剧本内容
    try:
        script = filmcollection.find_one({'_id': script_id})
        if script:
            # 返回剧本内容
            return jsonify({'success': True, 'content': script['content']}), 200
        else:
            return jsonify({'success': False, 'message': '未找到对应的剧本'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': f'查询失败: {str(e)}'}), 500

@app.route('/morescripts', methods=['POST'])
def get_more_scripts():
    # 检查请求中是否包含 JSON 数据
    if not request.is_json:
        return jsonify({'success': False, 'message': '请求数据不是 JSON 格式'}), 400

    # 获取 JSON 数据
    data = request.json

    # 从 JSON 数据中提取所需字段
    page = data.get('pageNum', 1)  # 默认第一页
    per_page = data.get('pageSize', 10)  # 默认每页显示10条记录
    search = data.get('search', '')

    try:
        # 尝试将 page 和 per_page 转换为整数
        page = int(page)
        per_page = int(per_page)
    except ValueError:
        return jsonify({'success': False, 'message': '页数或每页记录数应为整数'}), 400

    # 计算跳过的记录数
    skip = (page - 1) * per_page

    # 构建查询条件
    query = {}
    if search:
        regex = re.compile(search, re.IGNORECASE)
        query['title'] = {'$regex': regex}

    total_scripts = filmcollection.count_documents(query)

    # 查询 MongoDB 获取分页数据
    try:
        scripts = filmcollection.find(query).skip(skip).limit(per_page)

        # 将查询结果转换为列表，并将 ObjectId 转换为字符串
        scripts_list = [{'_id': str(script['_id']), 'title': script['title']} for script in scripts]

        return jsonify({'total': total_scripts, 'scripts': scripts_list}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'查询失败: {str(e)}'}), 500

@app.route('/scripts', methods=['POST'])
def get_scripts():
    # 检查请求中是否包含 JSON 数据
    if not request.is_json:
        return jsonify({'success': False, 'message': '请求数据不是 JSON 格式'}), 400

    # 获取 JSON 数据
    data = request.json

    # 从 JSON 数据中提取所需字段
    user_id = str(data.get('user_id'))
    page = data.get('pageNum', 1)  # 默认第一页
    per_page = data.get('pageSize', 10)  # 默认每页显示10条记录
    modify_time = data.get('modify_time')
    search=data.get('search')
    # 检查是否缺少必要字段
    if not user_id:
        return jsonify({'success': False, 'message': '缺少必要字段'}), 400

    try:
        # 尝试将 page 和 per_page 转换为整数
        page = int(page)
        per_page = int(per_page)
    except ValueError:
        return jsonify({'success': False, 'message': '页数或每页记录数应为整数'}), 400

    # 计算跳过的记录数
    skip = (page - 1) * per_page

    # 构建查询条件
    query = {'user_id': user_id}
    if modify_time:
        query['modify_time'] = {'$gte': modify_time}
    if search:
        regex = re.compile(search, re.IGNORECASE)
        query['script_name'] = {'$regex': regex}
    total_scripts = collection.count_documents(query)
    # 查询 MongoDB 获取分页数据
    try:
        scripts = collection.find(query).sort('modify_time', -1).skip(skip).limit(per_page)

        # 将查询结果转换为列表，并将 ObjectId 转换为字符串
        scripts_list = [{'_id': str(script['_id']), 'user_id': script['user_id'], 'modify_time': script['modify_time'],'script_name': script['script_name'], 'script_text': script['script_text'], 'note': script['note']} for script in scripts]
        
        return jsonify({ 'total':total_scripts,'scripts': scripts_list}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'查询失败: {str(e)}'}), 500

@app.route('/delete_scripts', methods=['POST'])
def delete_script():
    # 检查请求中是否包含 JSON 数据
    if not request.is_json:
        return jsonify({'success': False, 'message': '请求数据不是 JSON 格式'}), 400

    # 获取 JSON 数据
    data = request.json

    # 从 JSON 数据中提取剧本的 ID
    script_id = data.get('script_id')

    # 检查是否缺少必要字段
    if not script_id:
        return jsonify({'success': False, 'message': '缺少剧本 ID'}), 400

    try:
        # 尝试将 script_id 转换为 ObjectId
        script_id = ObjectId(script_id)
    except Exception as e:
        return jsonify({'success': False, 'message': '无效的剧本 ID'}), 400

    try:
        # 在 MongoDB 中删除相应的剧本记录
        result = collection.delete_one({'_id': script_id})

        if result.deleted_count == 1:
            return jsonify({'success': True, 'message': '剧本删除成功'}), 200
        else:
            return jsonify({'success': False, 'message': '未找到该剧本'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': f'剧本删除失败: {str(e)}'}), 500
  
@app.route('/upload', methods=['POST'])
def upload_file():
    # 检查请求中是否包含 JSON 数据
    if not request.is_json:
        return jsonify({'success': False, 'message': '请求数据不是 JSON 格式'}), 400

    # 获取 JSON 数据
    data = request.json

    # 从 JSON 数据中提取所需字段
    user_id = data.get('user_id')
    modify_time = data.get('修改时间')
    script_name=data.get('script_name')
    script_text = data.get('script_text')
    note = data.get('批注')

    # 检查是否缺少必要字段
    if not user_id or not modify_time or not script_text or not script_name:
        return jsonify({'success': False, 'message': '缺少必要字段'}), 400

    # 将修改时间转换为 datetime 对象
    try:
        modify_time = datetime.datetime.strptime(modify_time, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return jsonify({'success': False, 'message': '修改时间格式错误，应为 YYYY-MM-DD HH:MM:SS'}), 400

    # 插入数据到 MongoDB
    try:
        result = collection.insert_one({
            'user_id': user_id,
            'modify_time': modify_time,
            'script_name':script_name,
            'script_text': script_text,
            'note': note
        })
        return jsonify({'success': True, 'message': '数据上传成功', 'inserted_id': str(result.inserted_id)}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'数据上传失败: {str(e)}'}), 500

@app.route('/user/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')

    user = User.query.filter_by(user_name=username).first()
    if user and user.user_passwd == password:
        return jsonify({'success': True, 'message': '登录成功','user_id':str(user.user_id)}), 200
    else:
        return jsonify({'success': False, 'message': '用户名或密码错误'}), 401

if __name__ == '__main__':
    app.run(debug=True, port=10029)
