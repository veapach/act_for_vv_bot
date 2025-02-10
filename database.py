import aiosqlite
from config import DB_PATH, log_message
import asyncio
from datetime import datetime


class Database:
    def __init__(self):
        self.db_path = DB_PATH
        asyncio.run(self.initialize_db())

    async def initialize_db(self):
        await self.create_users_table()
        await self.create_reports_table() 
        await self.migrate_db()  

    async def migrate_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await self.check_and_add_column(db, "users", "first_name", "TEXT NOT NULL")
            await self.check_and_add_column(db, "users", "last_name", "TEXT NOT NULL")
            await self.check_and_add_column(db, "reports", "user_id", "INTEGER NOT NULL")
            await self.check_and_add_column(db, "reports", "telegram_message_id", "INTEGER")
            await self.check_and_add_column(db, "reports", "date", "TEXT NOT NULL")
            await self.check_and_add_column(db, "reports", "address", "TEXT NOT NULL")
            await db.commit()
        await log_message("Миграция базы данных завершена")

    async def check_and_add_column(self, db, table_name, column_name, column_type):
        cursor = await db.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in await cursor.fetchall()]
        if column_name not in columns:
            await db.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")

    async def create_users_table(self):
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

    async def get_reports(self, user_id: int, start_date: str, end_date: str):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT telegram_message_id FROM reports
                WHERE user_id = ? AND date BETWEEN ? AND ?
                """,
                (user_id, start_date, end_date)
            )
            return await cursor.fetchall()

    async def create_reports_table(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS reports (
                    report_id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    telegram_message_id INTEGER,
                    date TEXT NOT NULL,
                    address TEXT NOT NULL
                )
                """
            )
            await db.commit()

    async def add_report(self, user_id: int, telegram_message_id: int, date: str, address: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO reports (user_id, telegram_message_id, date, address)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, telegram_message_id, date, address),
            )
            await db.commit()

    async def get_reports_by_address(self, user_id: int, address: str):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT telegram_message_id FROM reports
                WHERE user_id = ? AND address = ?
                """,
                (user_id, address)
            )
            return await cursor.fetchall()