import aiosqlite
from config import DB_PATH, log_message


class Database:
    def __init__(self):
        self.db_path = DB_PATH

    async def create_user_table(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL
                )
                """
            )
            await db.commit()
            print("Таблица users создана или уже существует")

    async def add_user(self, user_id: int, first_name: str, last_name: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO users (user_id, first_name, last_name)
                VALUES (?, ?, ?)
                """,
                (user_id, first_name, last_name),
            )
            await db.commit()
        await log_message(f"Пользователь {user_id} добавлен в базу данных")

    async def get_user(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT first_name, last_name FROM users WHERE user_id = ?", (user_id,)
            )
            return await cursor.fetchone()

    async def update_user(self, user_id: int, first_name: str, last_name: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE users
                SET first_name = ?, last_name = ?
                WHERE user_id = ?
                """,
                (first_name, last_name, user_id),
            )
            await db.commit()
        await log_message(f"Пользователь {user_id} обновлен в базе данных")
