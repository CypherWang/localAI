import sqlite3

def initialize_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # 创建 sessions 表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_name TEXT NOT NULL
        )
    ''')

    # 创建 history 表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            session_id INTEGER NOT NULL,
            session_name TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    initialize_db()
