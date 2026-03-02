import sqlite3
import uuid

DB_NAME = "users.db"

# -------------------------
# CREATE TABLES
# -------------------------
def create_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # USERS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        name TEXT,
        email TEXT PRIMARY KEY,
        password TEXT,
        company TEXT
    )
    """)

    # CHATS (Added is_hidden column)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        chat_id TEXT PRIMARY KEY,
        email TEXT,
        company TEXT,
        title TEXT,
        is_hidden INTEGER DEFAULT 0
    )
    """)

    # MESSAGES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        chat_id TEXT,
        email TEXT,
        company TEXT,
        role TEXT,
        content TEXT,
        model TEXT,
        response_time REAL
    )
    """)

    conn.commit()
    conn.close()


# -------------------------
# SIGNUP
# -------------------------
def signup_user(name, email, password, company):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email=?", (email,))
    if cursor.fetchone():
        conn.close()
        return False

    cursor.execute(
        "INSERT INTO users (name, email, password, company) VALUES (?, ?, ?, ?)",
        (name, email, password, company)
    )

    conn.commit()
    conn.close()
    return True


# -------------------------
# LOGIN
# -------------------------
def login_user(email, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name, company FROM users WHERE email=? AND password=?",
        (email, password)
    )

    user = cursor.fetchone()
    conn.close()
    return user


# -------------------------
# CREATE NEW CHAT
# -------------------------
def create_new_chat(email, company):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    chat_id = str(uuid.uuid4())

    cursor.execute(
        "INSERT INTO chats (chat_id, email, company, title, is_hidden) VALUES (?, ?, ?, ?, 0)",
        (chat_id, email, company, "New Chat")
    )

    conn.commit()
    conn.close()
    return chat_id


# -------------------------
# UPDATE CHAT TITLE
# -------------------------
def update_chat_title(chat_id, title):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE chats SET title=? WHERE chat_id=?",
        (title, chat_id)
    )

    conn.commit()
    conn.close()


# -------------------------
# HIDE CHAT (SOFT DELETE)
# -------------------------
def hide_chat(chat_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE chats SET is_hidden=1 WHERE chat_id=?",
        (chat_id,)
    )

    conn.commit()
    conn.close()


# -------------------------
# GET USER CHATS (ONLY VISIBLE)
# -------------------------
def get_user_chats(email):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT chat_id, title 
        FROM chats 
        WHERE email=? AND is_hidden=0
        ORDER BY rowid DESC
    """, (email,))

    data = cursor.fetchall()
    conn.close()
    return data


# -------------------------
# SAVE MESSAGE
# -------------------------
def save_message(chat_id, email, company, role, content, model, response_time):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?, ?)",
        (chat_id, email, company, role, content, model, response_time)
    )

    conn.commit()
    conn.close()


# -------------------------
# LOAD CHAT MESSAGES
# -------------------------
def get_chat_messages(chat_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT role, content, model, response_time FROM messages WHERE chat_id=?",
        (chat_id,)
    )

    data = cursor.fetchall()
    conn.close()

    return [
        {
            "role": r,
            "content": c,
            "model": m,
            "response_time": t
        }
        for r, c, m, t in data
    ]


create_tables()