import sqlite3
import uuid

DB_NAME = "users.db"

# -------------------------
# SAFE COLUMN ADD FUNCTION
# -------------------------
def add_column_if_not_exists(cursor, table, column, column_type):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in cursor.fetchall()]
    if column not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")

# -------------------------
# CREATE / UPDATE TABLES
# -------------------------
def create_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # USERS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        name TEXT,
        email TEXT PRIMARY KEY,
        password TEXT
    )
    """)

    # CHATS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        chat_id TEXT PRIMARY KEY,
        email TEXT,
        title TEXT
    )
    """)

    # MESSAGES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        chat_id TEXT,
        role TEXT,
        content TEXT,
        model TEXT
    )
    """)

    # Safe Migration Columns
    add_column_if_not_exists(cursor, "users", "company", "TEXT")
    add_column_if_not_exists(cursor, "chats", "company", "TEXT")
    add_column_if_not_exists(cursor, "messages", "email", "TEXT")
    add_column_if_not_exists(cursor, "messages", "company", "TEXT")
    add_column_if_not_exists(cursor, "messages", "response_time", "REAL")

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
        "INSERT INTO chats (chat_id, email, company, title) VALUES (?, ?, ?, ?)",
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
# GET USER CHATS
# -------------------------
def get_user_chats(email):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT chat_id, title FROM chats WHERE email=? ORDER BY rowid DESC",
        (email,)
    )
    data = cursor.fetchall()
    conn.close()
    return data

# -------------------------
# SAVE MESSAGE
# -------------------------
def save_message(chat_id, email, company, role, content, model, response_time=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """INSERT INTO messages
           (chat_id, email, company, role, content, model, response_time)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
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

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "role": r,
            "content": c,
            "model": m,
            "response_time": t
        }
        for r, c, m, t in rows
    ]

create_tables()