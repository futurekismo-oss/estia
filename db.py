import sqlite3
from datetime import datetime

DB_NAME = "estia.db"


def init_database():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                minutes INTEGER,
                completed BOOLEAN
            )
            """)


def log_session(minutes: int, completed: bool):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT INTO sessions ( date, minutes, completed ) VALUES (?, ?, ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M"), minutes, completed),
        )
