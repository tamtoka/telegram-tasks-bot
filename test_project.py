"""Проверки ключевых требований задания без токена и сети."""

import csv
import io
import tempfile
import unittest
from pathlib import Path

from database import add_task, get_tasks, init_db
from export_csv import make_csv


class ProjectTests(unittest.TestCase):
    """Проверяет хранение и экспорт на отдельной временной базе."""

    def test_persistence_order_and_owners(self) -> None:
        """Повторная инициализация сохраняет порядок и разделение пользователей."""
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as directory:
            path = Path(directory) / "test.db"
            init_db(path)
            add_task("Первая 'задача'", 10, path)
            add_task("Чужая задача", 20, path)
            add_task("Вторая задача", 10, path)
            init_db(path)
            self.assertEqual(
                [row["text"] for row in get_tasks(10, path)],
                ["Первая 'задача'", "Вторая задача"],
            )
            self.assertEqual(len(get_tasks(20, path)), 1)
            self.assertEqual(get_tasks(30, path), [])
            self.assertTrue(get_tasks(10, path)[0]["created_at"])

    def test_csv_round_trip(self) -> None:
        """Кириллица, кавычки, переносы и разделители переживают экспорт и чтение."""
        text = 'Купить молоко; "сыр"\nИ хлеб'
        payload = make_csv([
            {"id": 1, "text": text, "user": 10, "created_at": "2026-10-21 10:00:00"},
            {"id": 2, "text": "=1+1", "user": 10, "created_at": "2026-10-21 10:01:00"},
        ])
        self.assertTrue(payload.startswith(b"\xef\xbb\xbf"))
        rows = list(csv.reader(io.StringIO(payload.decode("utf-8-sig")), delimiter=";"))
        self.assertEqual(rows[0][-2:], ["Статус", "Категория"])
        self.assertEqual(rows[1][1], text)
        self.assertEqual(rows[2][1], "'=1+1")
        self.assertTrue(all(len(row) == 6 for row in rows))


if __name__ == "__main__":
    unittest.main()
