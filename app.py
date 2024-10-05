import os
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, g
import bcrypt
from psycopg2 import connect, sql, extras
from dotenv import load_dotenv
import base64
import datetime
from datetime import timedelta, datetime
import torch
from ultralytics import YOLO  # 导入 YOLOv8
import pytz
from PIL import Image
import io
import numpy as np
from flask_cors import CORS
import jwt
from functools import wraps


from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *

# 加载环境变量
load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = 'your_secret_key'  # 用于加密 session，请替换为您的实际密钥

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')

# 获取数据库 URL
DATABASE_URL = os.getenv('EXTERNAL_DB_URL')

def get_db_connection():
    conn = connect(DATABASE_URL)
    return conn
    
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # JWT is passed in the request header
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'error': 'Token is missing!'}), 401
        try:
            # Decode the token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            g.user_id = data['user_id']
            g.bot_key = data['bot_key']
        except Exception as e:
            return jsonify({'error': 'Token is invalid!'}), 401
        return f(*args, **kwargs)
    return decorated

# 加载您的 YOLOv8 模型
model_2 = YOLO('./train2/weights/best.pt')
model_4 = YOLO('./train4/weights/best.pt')
model_7 = YOLO('./train7/weights/best.pt')

# 请替换为您自己的 Line Bot API 令牌和密钥
line_bot_api = LineBotApi('p2Vcx/FyOgJh+yzE5uQpl7D4zrMiIHFsdkqJ+6tVAh0SfJQ38eM/I4QhF3M2VNm100pezsvA2PPPEQ0EGk8wO4lmVG8PpMWzy9b8nKhLVNzvG+LJBgEXbDBs7P+jEabhKlHhVxJR2siY66R2n4NjrgdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('55c7e3abfc55dfa40f60fd5651da33e2')



# 注册路由
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    username = data.get('username')
    password = data.get('password')
    bot_key = data.get('bot_key')

    if not (name and username and password and bot_key):
        return jsonify({'error': '請填寫所有欄位'}), 400

    if len(password) < 6 or len(password) > 18:
        return jsonify({'error': '密碼長度需為6到18位數'}), 400
    if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        return jsonify({'error': '密碼必須包含英文字母和數字'}), 400

    # 使用 bcrypt 进行密码哈希
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 检查用户名是否已存在
        cursor.execute('SELECT id FROM Login_Info WHERE login_account = %s', (username,))
        if cursor.fetchone():
            return jsonify({"error": "用户名已存在"}), 400

        # 将加密的密码存入数据库
        cursor.execute('''
            INSERT INTO Login_Info (login_name, login_account, login_password, bot_key)
            VALUES (%s, %s, %s, %s)
        ''', (name, username, hashed_password, bot_key))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': '註冊成功'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logout')
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')

        # 确认用户是否提供账号与密码
        if not (username and password):
            return jsonify({'error': '請提供帳號和密碼'}), 400

        try:
            # 连接到数据库
            conn = get_db_connection()
            cursor = conn.cursor()

            # 查询数据库中的密码哈希值
            cursor.execute('''
                SELECT id, login_password, login_name FROM Login_Info WHERE login_account = %s
            ''', (username,))
            result = cursor.fetchone()

            cursor.close()
            conn.close()

            # 检查密码是否匹配
            if result and bcrypt.checkpw(password.encode('utf-8'), result[1].encode('utf-8')):
                # 密码匹配，存入 session
                session['user_id'] = result[0]  # 用户 ID
                session['username'] = username  # 用户账号
                session['name'] = result[2]     # 用户姓名

                # 登录成功后跳转至用户页面
                return jsonify({'message': '登入成功'}), 200
            else:
                return jsonify({'error': '帳號或密碼錯誤'}), 401
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # 当用户通过 GET 请求进入 /login，渲染 index.html
    return render_template('index.html')

# 用户专属页面路由
@app.route('/user_page')
def user_page():
    if 'user_id' in session:
        # 获取 session 中的用户资料
        user_id = session['user_id']
        username = session['username']
        name = session['name']

        # 从数据库中获取长者信息和最近的紧急事件
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 获取用户的 bot_key
            cursor.execute('SELECT bot_key FROM Login_Info WHERE id = %s', (user_id,))
            bot_key = cursor.fetchone()[0]

            # 获取长者信息
            cursor.execute('''
                SELECT elder_id, region_id, elder_name FROM Elder_Info WHERE bot_key = %s
            ''', (bot_key,))
            elders = cursor.fetchall()

            # 获取最近的紧急事件
            cursor.execute('''
                SELECT region_id, emergency_message, emergency_time FROM Emergency_Info WHERE bot_key = %s ORDER BY emergency_time DESC LIMIT 10
            ''', (bot_key,))
            emergencies = cursor.fetchall()

            cursor.close()
            conn.close()
        except Exception as e:
            return jsonify({'error': str(e)}), 500

        # 渲染模板并传递用户资料和长者信息
        return render_template('using.html', name=name, username=username, elders=elders, emergencies=emergencies)
    else:
        return redirect(url_for('login'))  # 如果未登录则跳转到登录页面

@app.route('/reset_password', methods=['POST'])
def reset_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    data = request.json
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    confirm_new_password = data.get('confirm_new_password')

    # 检查新密码与重复输入的密码是否一致
    if new_password != confirm_new_password:
        return jsonify({'error': '新密碼與重複輸入不一致'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 查询当前密码
        cursor.execute('SELECT login_password FROM Login_Info WHERE id = %s', (session['user_id'],))
        result = cursor.fetchone()

        # 检查旧密码是否正确
        if not bcrypt.checkpw(old_password.encode('utf-8'), result[0].encode('utf-8')):
            return jsonify({'error': '舊密碼不正確'}), 400

        # 更新密码
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute('''
            UPDATE Login_Info
            SET login_password = %s
            WHERE id = %s
        ''', (hashed_password, session['user_id']))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': '更新成功'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Bot Key 重设路由
@app.route('/reset_botkey', methods=['POST'])
def reset_botkey():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    data = request.json
    new_bot_key = data.get('new_bot_key')

    if not new_bot_key:
        return jsonify({'error': '請提供新的 Bot Key'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 更新 Bot Key
        cursor.execute('''
            UPDATE Login_Info
            SET bot_key = %s
            WHERE id = %s
        ''', (new_bot_key, session['user_id']))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': '更新成功'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_emergencies', methods=['GET'])
def get_emergencies():
    if 'user_id' in session:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 获取用户的 bot_key
            cursor.execute('SELECT bot_key FROM Login_Info WHERE id = %s', (session['user_id'],))
            bot_key = cursor.fetchone()[0]

            # 获取最近的紧急事件
            cursor.execute('''
                SELECT region_id, emergency_message, emergency_time, urgency FROM Emergency_Info 
                WHERE bot_key = %s ORDER BY emergency_time DESC LIMIT 10
            ''', (bot_key,))
            emergencies = cursor.fetchall()

            cursor.close()
            conn.close()

            # 将数据转换为 JSON 格式返回
            emergency_data = [{
                'region_id': emergency[0],
                'emergency_message': emergency[1],
                'emergency_time': emergency[2].strftime('%Y-%m-%d %H:%M:%S'),
                'urgency': emergency[3]
            } for emergency in emergencies]

            return jsonify(emergency_data), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/clear_emergencies', methods=['DELETE'])
def clear_emergencies():
    if 'user_id' in session:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 获取用户的 bot_key
            cursor.execute('SELECT bot_key FROM Login_Info WHERE id = %s', (session['user_id'],))
            bot_key = cursor.fetchone()[0]

            # 删除该用户的所有紧急事件
            cursor.execute('DELETE FROM Emergency_Info WHERE bot_key = %s', (bot_key,))
            conn.commit()

            cursor.close()
            conn.close()

            return jsonify({'message': '清除成功'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': '未登入'}), 401

# 新增长者及卡片显示
@app.route('/add_elder', methods=['POST'])
def add_elder():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    data = request.json
    elder_name = data.get('elder_name')
    region_id = data.get('region_id')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 获取用户的 bot_key
        cursor.execute('SELECT bot_key FROM Login_Info WHERE id = %s', (session['user_id'],))
        bot_key = cursor.fetchone()[0]

        cursor.execute('''
            INSERT INTO Elder_Info (region_id, elder_name, bot_key)
            VALUES (%s, %s, %s)
        ''', (region_id, elder_name, bot_key))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': '長者新增成功'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/upload_photo', methods=['POST'])
def upload_photo():
    data = request.get_json()
    bot_key = data.get('bot_key')
    photo_data = data.get('photo_data')  # 這應該是 base64 編碼的照片

    if not bot_key or not photo_data:
        return jsonify({'error': '缺少 bot_key 或 photo_data'}), 400

    try:
        # 解析照片資料
        photo_bytes = base64.b64decode(photo_data)
        img = Image.open(io.BytesIO(photo_bytes))

        # 將 PIL Image 轉換為 NumPy 數組以便 YOLO 處理
        img_np = np.array(img)

        # 使用 YOLOv8 模型進行推理
        results_2 = model_2(img_np)  # YOLO 模型返回結果列表
        results_4 = model_4(img_np)
        results_7 = model_7(img_np)

        # 創建對應的資料夾以保存照片（如果不存在）
        save_dir = os.path.join('static', 'photos', bot_key)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # 繪製並保存推理結果
        result_img_2 = results_2[0].plot()  # 使用 plot() 繪製 YOLO 推理結果
        result_img_4 = results_4[0].plot()
        result_img_7 = results_7[0].plot()

        # 定義圖片文件名
        filename_model2 = f'{bot_key}_model2.jpg'
        filename_model4 = f'{bot_key}_model4.jpg'
        filename_model7 = f'{bot_key}_model7.jpg'

        # 將繪製好的圖片保存
        Image.fromarray(result_img_2).save(os.path.join(save_dir, filename_model2))
        Image.fromarray(result_img_4).save(os.path.join(save_dir, filename_model4))
        Image.fromarray(result_img_7).save(os.path.join(save_dir, filename_model7))

        # 將檢測結果存入資料庫
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO Detection_Records (bot_key, model_name, image_path)
            VALUES (%s, %s, %s)
        ''', (bot_key, 'model2', os.path.join(save_dir, filename_model2)))
        cursor.execute('''
            INSERT INTO Detection_Records (bot_key, model_name, image_path)
            VALUES (%s, %s, %s)
        ''', (bot_key, 'model4', os.path.join(save_dir, filename_model4)))
        cursor.execute('''
            INSERT INTO Detection_Records (bot_key, model_name, image_path)
            VALUES (%s, %s, %s)
        ''', (bot_key, 'model7', os.path.join(save_dir, filename_model7)))

        # 檢查 model7 是否檢測到 'fallen' 且信心度高於 0.7
        fallen_detected = False
        fallen_confidence = 0.0  # 初始化信心度

        for box in results_7[0].boxes:
            class_id = int(box.cls)
            class_name = model_7.names.get(class_id, "")
            confidence = float(box.conf)
            if class_name.lower() == 'fallen' and confidence >= 0.7:
                fallen_detected = True
                fallen_confidence = confidence
                break

        if fallen_detected:
            # 獲取用戶的 region_id（假設每個用戶有一個或多個長者，每個長者有 region_id）
            cursor.execute('''
                SELECT DISTINCT region_id FROM Elder_Info WHERE bot_key = %s
            ''', (bot_key,))
            regions = cursor.fetchall()
            regions = [region[0] for region in regions]

            # 獲取當前 UTC 時間並轉換為台灣時間
            utc_now = datetime.utcnow()
            taiwan_tz = pytz.timezone('Asia/Taipei')
            taiwan_time = utc_now.replace(tzinfo=pytz.utc).astimezone(taiwan_tz)
            formatted_time = taiwan_time.strftime('%Y-%m-%d %H:%M:%S')

            # 獲取關聯的 Line IDs
            cursor.execute('SELECT line_id FROM Line_IDs WHERE bot_key = %s', (bot_key,))
            line_ids = cursor.fetchall()
            line_ids = [line_id[0] for line_id in line_ids]

            # 構建緊急事件消息，包含信心度
            emergency_message = f'偵測到長者跌倒 (辨識率: {fallen_confidence:.2f})'
            if not line_ids:
                emergency_message += ' (LINE未設定)'

            for region_id in regions:
                cursor.execute('''
                    INSERT INTO Emergency_Info (region_id, emergency_message, bot_key, urgency, emergency_time, confidence)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (region_id, emergency_message, bot_key, '3', formatted_time, fallen_confidence))

            conn.commit()

            # 構建圖片的公開 URL
            base_url = os.getenv('BASE_URL', 'https://e726-163-32-88-31.ngrok-free.app')  # 確保使用 HTTPS
            image_url = f"{base_url}/static/photos/{bot_key}/{filename_model7}"

            # 構建消息列表
            messages = [TextSendMessage(text=emergency_message)]

            if line_ids:
                # 如果有 LINE IDs，添加圖片消息
                messages.append(ImageSendMessage(
                    original_content_url=image_url,
                    preview_image_url=image_url
                ))

            # 發送 LINE 通知
            if line_ids:
                for line_id in line_ids:
                    try:
                        line_bot_api.push_message(line_id, messages)
                    except Exception as e:
                        print(f"Error sending message to LINE ID {line_id}: {str(e)}")

        cursor.close()
        conn.close()

        return jsonify({'message': '照片上傳並識別成功'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500




@app.route('/<string:region_id>/<string:bot_key>/<string:light_io>/<string:urgency>', methods=['GET'])
def handle_light_change(region_id, bot_key, light_io, urgency):
    try:
        # 根据 bot_key 找到对应的用户或设备
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id FROM Login_Info WHERE bot_key = %s
        ''', (bot_key,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'error': '無效的 bot_key'}), 400

        # 将灯条状态存入数据库，使用 region_id
        cursor.execute('''
            INSERT INTO Light_On_Record (region_id, bot_key)
            VALUES (%s, %s)
        ''', (region_id, bot_key))  # region_id 是从 URL 路径中获得的

        # 如果 light_io 为 1，则记录紧急事件（检测到长者 => 灯条亮起）
        if light_io == '1':  # 确保 light_io 为字符串 '1'
            emergency_message = '偵測到長者，燈條亮起'

            # 获取当前 UTC 时间并转换为台湾时间
            utc_now = datetime.utcnow()
            taiwan_tz = pytz.timezone('Asia/Taipei')
            taiwan_time = utc_now.replace(tzinfo=pytz.utc).astimezone(taiwan_tz)
            formatted_time = taiwan_time.strftime('%Y-%m-%d %H:%M:%S')  # 去掉秒的小数

            # 记录紧急事件，包含台湾时间、区域和紧急程度
            cursor.execute('''
                INSERT INTO Emergency_Info (region_id, emergency_message, bot_key, emergency_time, urgency)
                VALUES (%s, %s, %s, %s, %s)
            ''', (region_id, emergency_message, bot_key, formatted_time, urgency))

            # 查找所有与该 bot_key 相关的 LINE ID
            cursor.execute('SELECT line_id FROM Line_IDs WHERE bot_key = %s', (bot_key,))
            line_ids = cursor.fetchall()

            # 发送通知给每个 LINE ID
            for line_id_tuple in line_ids:
                line_id = line_id_tuple[0]
                try:
                    line_bot_api.push_message(line_id, TextMessage(text=emergency_message))
                except Exception as e:
                    print(f"Error sending message to LINE ID {line_id}: {str(e)}")

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': '燈條狀態已更新，並發送通知'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/get_latest_photos', methods=['GET'])
def get_latest_photos():
    if 'user_id' in session:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 获取用户的 bot_key
            cursor.execute('SELECT bot_key FROM Login_Info WHERE id = %s', (session['user_id'],))
            bot_key = cursor.fetchone()[0]

            # 获取请求中的页数和每页显示数量
            page = int(request.args.get('page', 1))  # 默认为第 1 页
            per_page = int(request.args.get('per_page', 5))  # 每页显示 5 张图片

            offset = (page - 1) * per_page

            # 查找与该 bot_key 相关的图片并进行分页
            cursor.execute('''
                SELECT image_path FROM Detection_Records 
                WHERE bot_key = %s 
                ORDER BY detected_at DESC
                LIMIT %s OFFSET %s
            ''', (bot_key, per_page, offset))
            results = cursor.fetchall()

            # 查询总图片数量，计算总页数
            cursor.execute('SELECT COUNT(*) FROM Detection_Records WHERE bot_key = %s', (bot_key,))
            total_images = cursor.fetchone()[0]
            total_pages = (total_images + per_page - 1) // per_page  # 总页数

            cursor.close()
            conn.close()

            if results:
                base_url = os.getenv('BASE_URL', 'https://e726-163-32-88-31.ngrok-free.app')
                photo_urls = [f"{base_url}/{result[0]}" for result in results]  # 构建完整的 URL
                return jsonify({
                    'photo_urls': photo_urls,
                    'current_page': page,
                    'total_pages': total_pages
                }), 200
            else:
                return jsonify({'error': '無偵測圖片記錄'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': '未登入'}), 401

@app.route('/data', methods=['GET'])
def data():
    return render_template('test_table.html')

# LINE Bot 部分
@app.route('/callback', methods=['POST'])
def callback():
    # 获取 X-Line-Signature header 值
    signature = request.headers['X-Line-Signature']

    # 获取请求 body 内容
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 处理 webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id  # 获取发消息者的 user_id
    message_text = event.message.text  # 获取发送的消息内容

    # 检查消息格式是否为 'botkey=XXXXX'
    if message_text.startswith("botkey="):
        bot_key = message_text.split('=')[1]  # 获取 bot_key

        # 将 line_id 和 bot_key 存入数据库
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 插入新的 line_id 和 bot_key 配对
            cursor.execute('''
                INSERT INTO Line_IDs (line_id, bot_key)
                VALUES (%s, %s)
            ''', (user_id, bot_key))

            conn.commit()
            cursor.close()
            conn.close()

            # 回复用户
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="您的 bot_key 已成功設定!")
            )
        except Exception as e:
            print(f"Database error: {str(e)}")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="儲存 bot_key 時發生錯誤，請稍後再試。")
            )
    else:
        # 处理其他消息
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請輸入 'botkey=您的 bot_key'")
        )
        
        
#-----------------------------------------------------------------------------------------------------------------------#
# API 部分

@app.route('/API')
def API_index():
    return jsonify({"message": "Welcome to the Elder Care Flask API"})

# User registration
@app.route('/API_register', methods=['POST'])
def API_register():
    data = request.json
    name = data.get('name')
    username = data.get('username')
    password = data.get('password')
    bot_key = data.get('bot_key')

    if not (name and username and password and bot_key):
        return jsonify({"error": "Please provide all required fields"}), 400

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if username already exists
        cursor.execute('SELECT id FROM Login_Info WHERE login_account = %s', (username,))
        if cursor.fetchone():
            return jsonify({"error": "Username already exists"}), 400

        # Insert user data into the database
        cursor.execute('''
            INSERT INTO Login_Info (login_name, login_account, login_password, bot_key)
            VALUES (%s, %s, %s, %s)
        ''', (name, username, hashed_password.decode('utf-8'), bot_key))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "註冊成功"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# User login
@app.route('/API_login', methods=['POST'])
def API_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not (username and password):
        return jsonify({"error": "Please provide username and password"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch user data
        cursor.execute('SELECT id, login_password, bot_key FROM Login_Info WHERE login_account = %s', (username,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
            # Generate token
            token = jwt.encode({
                'user_id': user[0],
                'bot_key': user[2],
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, app.config['SECRET_KEY'], algorithm="HS256")
            return jsonify({"message": "登入成功", "token": token}), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# Get user info
@app.route('/API_get_user_info', methods=['GET'])
@token_required
def API_get_user_info():
    try:
        user_id = g.user_id
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT login_name, login_account FROM Login_Info WHERE id = %s', (user_id,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:
            return jsonify({
                "name": user[0],
                "username": user[1]
            }), 200
        else:
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# 刪除長者
@app.route('/API_delete_elder', methods=['DELETE'])
@token_required
def API_delete_elder():
    data = request.get_json()
    elder_id = data.get('elder_id')

    if not elder_id:
        return jsonify({'error': '缺少 elder_id'}), 400

    try:
        bot_key = g.bot_key
        conn = get_db_connection()
        cursor = conn.cursor()

        # 刪除只屬於當前用戶的長者
        cursor.execute("DELETE FROM Elder_Info WHERE elder_id = %s AND bot_key = %s", (elder_id, bot_key))
        conn.commit()

        # 檢查是否有刪除
        if cursor.rowcount == 0:
            return jsonify({'error': '找不到該長者或無權刪除'}), 404

        return jsonify({'message': '長者刪除成功'}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': '伺服器錯誤'}), 500
    finally:
        cursor.close()
        conn.close()

# 刪除所有列表記錄
@app.route('/API_delete_all_records', methods=['DELETE'])
@token_required
def API_delete_all_records():
    try:
        bot_key = g.bot_key
        conn = get_db_connection()
        cursor = conn.cursor()

        # 将表名改为小写
        tables_to_clear = ['emergency_info', 'light_on_record', 'detection_records']

        for table in tables_to_clear:
            # 直接使用字符串格式化，但确保表名安全
            query = f"DELETE FROM {table} WHERE bot_key = %s"
            cursor.execute(query, (bot_key,))

        conn.commit()

        return jsonify({'message': '所有列表记录删除成功'}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': '服务器错误'}), 500
    finally:
        cursor.close()
        conn.close()
        
@app.route('/API_get_emergencies', methods=['GET'])
@token_required
def API_get_emergencies():
    try:
        bot_key = g.bot_key
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=extras.DictCursor)

        cursor.execute('''
            SELECT region_id, emergency_message, emergency_time, urgency FROM Emergency_Info 
            WHERE bot_key = %s ORDER BY emergency_time DESC
        ''', (bot_key,))
        emergencies = cursor.fetchall()

        cursor.close()
        conn.close()

        emergency_list = [dict(emergency) for emergency in emergencies]

        return jsonify({'emergencies': emergency_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Reset password
@app.route('/API_reset_password', methods=['POST'])
@token_required
def API_reset_password():
    data = request.json
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    confirm_new_password = data.get('confirm_new_password')

    if not (old_password and new_password and confirm_new_password):
        return jsonify({"error": "Please provide all required fields"}), 400

    if new_password != confirm_new_password:
        return jsonify({"error": "New passwords do not match"}), 400

    try:
        user_id = g.user_id
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch old password
        cursor.execute('SELECT login_password FROM Login_Info WHERE id = %s', (user_id,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(old_password.encode('utf-8'), user[0].encode('utf-8')):
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            # Update password
            cursor.execute('UPDATE Login_Info SET login_password = %s WHERE id = %s', (hashed_password, user_id))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"message": "更新成功"}), 200
        else:
            cursor.close()
            conn.close()
            return jsonify({"error": "Old password is incorrect"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/API_get_elders', methods=['GET'])
@token_required
def API_get_elders():
    try:
        bot_key = g.bot_key
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=extras.DictCursor)

        cursor.execute('''
            SELECT elder_id, region_id, elder_name FROM Elder_Info WHERE bot_key = %s
        ''', (bot_key,))
        elders = cursor.fetchall()

        cursor.close()
        conn.close()

        elder_list = [dict(elder) for elder in elders]

        return jsonify({'elders': elder_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Reset bot key
@app.route('/API_reset_botkey', methods=['POST'])
@token_required
def API_reset_botkey():
    data = request.json
    new_bot_key = data.get('new_bot_key')

    if not new_bot_key:
        return jsonify({"error": "Please provide the new bot key"}), 400

    try:
        user_id = g.user_id
        conn = get_db_connection()
        cursor = conn.cursor()

        # Update bot key
        cursor.execute('UPDATE Login_Info SET bot_key = %s WHERE id = %s', (new_bot_key, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "更新成功"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Add elder
@app.route('/API_add_elder', methods=['POST'])
@token_required
def API_add_elder():
    data = request.json
    elder_name = data.get('elder_name')
    region_id = data.get('region_id')

    if not (elder_name and region_id):
        return jsonify({"error": "Please provide all required fields"}), 400

    try:
        bot_key = g.bot_key
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert elder data into the database
        cursor.execute('''
            INSERT INTO Elder_Info (elder_name, region_id, bot_key)
            VALUES (%s, %s, %s)
        ''', (elder_name, region_id, bot_key))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "長者新增成功"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get latest photos (assuming stored in Detection_Records)
@app.route('/API_get_latest_photos', methods=['GET'])
@token_required
def API_get_latest_photos():
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=5, type=int)

    try:
        bot_key = g.bot_key
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=extras.DictCursor)

        # Get total count
        cursor.execute('SELECT COUNT(*) FROM Detection_Records WHERE bot_key = %s', (bot_key,))
        total_count = cursor.fetchone()[0]
        total_pages = (total_count + per_page - 1) // per_page

        offset = (page - 1) * per_page

        # Fetch photo paths
        cursor.execute('''
            SELECT image_path FROM Detection_Records
            WHERE bot_key = %s
            ORDER BY detected_at DESC
            LIMIT %s OFFSET %s
        ''', (bot_key, per_page, offset))

        photos = cursor.fetchall()

        # Construct full URLs for the images
        base_url = os.getenv('BASE_URL', 'https://e726-163-32-88-31.ngrok-free.app')
        photo_urls = [f"{base_url}/{photo['image_path']}" for photo in photos]

        cursor.close()
        conn.close()

        return jsonify({
            'photo_urls': photo_urls,
            'current_page': page,
            'total_pages': total_pages
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # 确保照片目录存在
    if not os.path.exists(os.path.join('static', 'photos')):
        os.makedirs(os.path.join('static', 'photos'))
    app.run(debug=True, host='0.0.0.0', port=5011)