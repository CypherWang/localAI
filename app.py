from flask import Flask, request, jsonify, g, render_template
import sqlite3
import requests

app = Flask(__name__)
DATABASE = 'database.db'


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

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT session_name FROM sessions WHERE id = ?', (session_id,))
    session_name = cursor.fetchone()['session_name']

    cursor.execute('INSERT INTO history (role, content, session_id, session_name) VALUES (?, ?, ?, ?)',
                   ('user', user_input, session_id, session_name))
    db.commit()

    response = requests.post(
        'http://localhost:1234/v1/chat/completions',
        headers={
            'Content-Type': 'application/json',
            'Authorization': 'Bearer lm-studio'
        },
        json={
            'model': 'bartowski/gemma-2-9b-it-GGUF',
            'messages': [{'role': 'user', 'content': user_input}]
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
