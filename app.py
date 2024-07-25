from flask import Flask, render_template, request, jsonify, g
import sqlite3
import requests

app = Flask(__name__)

DATABASE = 'chat.db'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                session_id INTEGER NOT NULL
            )
        ''')
        db.commit()


init_db()


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    db = get_db()
    cursor = db.cursor()

    user_input = request.json.get('message')
    session_id = request.json.get('session_id', 1)  # 默认使用会话ID 1
    if user_input:
        cursor.execute('INSERT INTO history (role, content, session_id) VALUES (?, ?, ?)',
                       ('user', user_input, session_id))
        db.commit()

        # 请求本地部署的语言模型 API
        response = requests.post(
            'http://localhost:1234/v1/chat/completions',
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'Bearer lm-studio'
            },
            json={
                'model': 'Qwen/Qwen2-0.5B-Instruct-GGUF',
                'messages': [{'role': 'user', 'content': user_input}]
            }
        )
        data = response.json()
        assistant_reply = data['choices'][0]['message']['content']

        cursor.execute('INSERT INTO history (role, content, session_id) VALUES (?, ?, ?)',
                       ('assistant', assistant_reply, session_id))
        db.commit()

        return jsonify({'reply': assistant_reply})
    return jsonify({'reply': ''})


@app.route('/sessions', methods=['GET'])
def get_sessions():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT DISTINCT session_id FROM history')
    sessions = cursor.fetchall()
    return jsonify([session[0] for session in sessions])


@app.route('/history/<int:session_id>', methods=['GET'])
def get_history(session_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT role, content FROM history WHERE session_id = ?', (session_id,))
    history = cursor.fetchall()
    return jsonify([{'role': role, 'content': content} for role, content in history])


@app.route('/admin')
def admin():
    return render_template('admin.html')


@app.route('/admin/data')
def admin_data():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM history')
    data = cursor.fetchall()
    return jsonify(data)


if __name__ == '__main__':
    app.run(debug=True)
