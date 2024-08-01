from flask import Flask, request, jsonify, g, render_template
import sqlite3
import requests
import re
import logging

logging.basicConfig(level=logging.DEBUG)


app = Flask(__name__)
DATABASE = 'database.db'

# 添加天气API密钥（请在部署时替换为实际密钥）
WEATHER_API_KEY = '57296597bde24e9f963f60a484405f42'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


def get_weather(location_id):
    logging.debug(f"Attempting to get weather for location ID: {location_id}")
    url = f"https://devapi.qweather.com/v7/weather/now"
    params = {
        'location': location_id,
        'key': WEATHER_API_KEY
    }

    try:
        response = requests.get(url, params=params)
        logging.debug(f"API response status code: {response.status_code}")
        logging.debug(f"API response content: {response.text}")

        data = response.json()

        if response.status_code == 200 and data['code'] == '200':
            weather = data.get('now', {})
            weather_info = []

            if 'text' in weather:
                weather_info.append(f"天气：{weather['text']}")
            if 'temp' in weather:
                weather_info.append(f"温度：{weather['temp']}°C")
            if 'feelsLike' in weather:
                weather_info.append(f"体感温度：{weather['feelsLike']}°C")
            if 'humidity' in weather:
                weather_info.append(f"相对湿度：{weather['humidity']}%")
            if 'windDir' in weather:
                weather_info.append(f"风向：{weather['windDir']}")
            if 'windSpeed' in weather:
                weather_info.append(f"风速：{weather['windSpeed']}公里/小时")

            if weather_info:
                return f"LocationID {location_id} 的天气：" + "，".join(weather_info)
            else:
                return f"获取到 LocationID {location_id} 的天气数据，但没有具体信息。"
        else:
            logging.error(f"Failed to get weather. Status code: {response.status_code}, Response: {data}")
            return f"获取 LocationID {location_id} 的天气信息失败：{data.get('code', 'Unknown error')}"

    except requests.RequestException as e:
        logging.error(f"Request error: {str(e)}")
        return f"请求 LocationID {location_id} 的天气时发生错误：{str(e)}"
    except Exception as e:
        logging.error(f"Unexpected error in get_weather: {str(e)}")
        return f"获取 LocationID {location_id} 的天气时发生未知错误：{str(e)}"


def preprocess_input(user_input):
    weather_pattern = r'\[WEATHER:(.*?)\]'
    weather_queries = re.findall(weather_pattern, user_input)
    logging.debug(f"Preprocessing input: {user_input}")

    enhanced_input = user_input
    for query in weather_queries:
        weather_info = get_weather(query)
        enhanced_input = enhanced_input.replace(f'[WEATHER:{query}]', weather_info)

    return enhanced_input

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/admin')
def admin():
    return render_template('admin.html')


@app.route('/sessions', methods=['GET'])
def get_sessions():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id, session_name FROM sessions')
    sessions = [{'session_id': row['id'], 'session_name': row['session_name']} for row in cursor.fetchall()]
    return jsonify(sessions)


@app.route('/session', methods=['POST'])
def create_session():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO sessions (session_name) VALUES (?)', ('New Session',))
    session_id = cursor.lastrowid
    db.commit()
    return jsonify({'session_id': session_id, 'session_name': 'New Session'})


@app.route('/session/<int:session_id>', methods=['PUT'])
def rename_session(session_id):
    new_name = request.json.get('session_name')
    db = get_db()
    cursor = db.cursor()
    cursor.execute('UPDATE sessions SET session_name = ? WHERE id = ?', (new_name, session_id))
    db.commit()
    return jsonify({'status': 'success'})


@app.route('/session/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM sessions WHERE id = ?', (session_id,))
    cursor.execute('DELETE FROM history WHERE session_id = ?', (session_id,))
    db.commit()
    return jsonify({'status': 'success'})


@app.route('/history/<int:session_id>', methods=['GET'])
def get_history(session_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT role, content FROM history WHERE session_id = ? ORDER BY id ASC', (session_id,))
    messages = [{'role': row['role'], 'content': row['content']} for row in cursor.fetchall()]
    return jsonify(messages)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    session_id = data['session_id']
    user_input = data['message']
    logging.debug(f"Received chat request: {request.json}")
    # 预处理用户输入
    enhanced_input = preprocess_input(user_input)

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT session_name FROM sessions WHERE id = ?', (session_id,))
    session_name = cursor.fetchone()['session_name']

    cursor.execute('INSERT INTO history (role, content, session_id, session_name) VALUES (?, ?, ?, ?)',
                   ('user', user_input, session_id, session_name))
    db.commit()

    # 使用增强的输入调用 LLM
    response = requests.post(
        'http://localhost:1234/v1/chat/completions',
        headers={
            'Content-Type': 'application/json',
            'Authorization': 'Bearer lm-studio'
        },
        json={
            'model': 'bartowski/gemma-2-9b-it-GGUF',
            'messages': [{'role': 'user', 'content': enhanced_input}]
        }
    )
    data = response.json()
    assistant_reply = data['choices'][0]['message']['content']

    cursor.execute('INSERT INTO history (role, content, session_id, session_name) VALUES (?, ?, ?, ?)',
                   ('assistant', assistant_reply, session_id, session_name))
    db.commit()

    return jsonify({'reply': assistant_reply})


@app.route('/admin/data', methods=['GET'])
def get_admin_data():
    db = get_db()
    cursor = db.cursor()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    offset = (page - 1) * per_page

    cursor.execute('''
        SELECT h.id, h.role, h.content, h.session_id, s.session_name
        FROM history h
        JOIN sessions s ON h.session_id = s.id
        ORDER BY h.id DESC
        LIMIT ? OFFSET ?
    ''', (per_page, offset))

    data = [{'id': row['id'], 'role': row['role'], 'content': row['content'],
             'session_id': row['session_id'], 'session_name': row['session_name']}
            for row in cursor.fetchall()]

    return jsonify(data)


if __name__ == '__main__':
    app.run(debug=True)
