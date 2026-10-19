import os
import mysql.connector

def load_env(filepath=None):
    if filepath is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = os.path.join(base_dir, '.env')
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ.setdefault(key.strip(), val.strip())

load_env()

def get_connection():
    load_env()
    host = os.environ.get('DB_HOST', '127.0.0.1')
    port = int(os.environ.get('DB_PORT', 3306))
    database = os.environ.get('DB_NAME', 'ebbline')
    user = os.environ.get('DB_USER', 'ebbline')
    password = os.environ.get('DB_PASSWORD', 'ebbline_password')
    unix_socket = os.environ.get('DB_SOCKET', '')

    config = {
        'database': database,
        'user': user,
        'password': password,
        'autocommit': True,
    }
    if unix_socket and os.path.exists(unix_socket):
        config['unix_socket'] = unix_socket
    else:
        config['host'] = host
        config['port'] = port

    return mysql.connector.connect(**config)

def execute_query(sql, params=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params or ())
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()

def fetch_all(sql, params=None, dictionary=True):
    conn = get_connection()
    cursor = conn.cursor(dictionary=dictionary)
    try:
        cursor.execute(sql, params or ())
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def fetch_one(sql, params=None, dictionary=True):
    conn = get_connection()
    cursor = conn.cursor(dictionary=dictionary)
    try:
        cursor.execute(sql, params or ())
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

def call_proc(proc_name, args=()):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        result_args = cursor.callproc(proc_name, args)
        conn.commit()
        return result_args
    finally:
        cursor.close()
        conn.close()
