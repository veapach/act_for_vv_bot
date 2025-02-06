import sqlite3
from sqlite3 import Connection
from config import DB_PATH, log_message

class Database:
    def __init__(self):
        self.conn: Connection = sqlite3.connect(DB_PATH)
        self.create_user_table()

    def create_user_table(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL
                )
            """)
            log_message("Таблица users создана или уже существует")

    def add_user(self, user_id: int, first_name: str, last_name: str):
        with self.conn:
            self.conn.execute("""
                INSERT INTO users (user_id, first_name, last_name)
                VALUES (?, ?, ?)
            """, (user_id, first_name, last_name))
            log_message(f"Пользователь {user_id} добавлен в базу данных")

    def get_user(self, user_id: int):
        cursor = self.conn.cursor()
        cursor.execute("SELECT first_name, last_name FROM users WHERE user_id = ?", (user_id,))
        return cursor.fetchone()

    def update_user(self, user_id: int, first_name: str, last_name: str):
        with self.conn:
            self.conn.execute("""
                UPDATE users
                SET first_name = ?, last_name = ?
                WHERE user_id = ?
            """, (first_name, last_name, user_id))
            log_message(f"Пользователь {user_id} обновлён в базе данных") 
