"""Хранение задач в SQLite: файл базы сохраняется между запусками."""

import sqlite3
from contextlib import closing
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "tasks.db"


def init_db(db_path: Path = DB_PATH) -> None:
    """Создаёт таблицу при первом запуске, сохраняя существующие задачи."""
    with closing(sqlite3.connect(db_path)) as connection, connection:
        connection.execute(
            '''CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                user INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )'''
        )


def add_task(text: str, user_id: int, db_path: Path = DB_PATH) -> int:
    """Сохраняет задачу владельца и возвращает её номер."""
    with closing(sqlite3.connect(db_path)) as connection, connection:
        cursor = connection.execute(
            "INSERT INTO tasks (text, user) VALUES (?, ?)", (text, user_id)
        )
        return cursor.lastrowid


def get_tasks(user_id: int, db_path: Path = DB_PATH) -> list[sqlite3.Row]:
    """Возвращает только задачи указанного пользователя в порядке добавления."""
    with closing(sqlite3.connect(db_path)) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(
            "SELECT id, text, user, created_at FROM tasks WHERE user = ? ORDER BY id",
            (user_id,),
        ).fetchall()
