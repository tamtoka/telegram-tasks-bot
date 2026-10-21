"""Формирование CSV для Excel и LibreOffice без временных файлов."""

import csv
import io
from collections.abc import Iterable, Mapping
from typing import Any


def make_csv(tasks: Iterable[Mapping[str, Any]]) -> bytes:
    """Экспортирует задачи; две дополнительные колонки оставлены для эксперимента."""
    output = io.StringIO(newline="")
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["ID", "Задача", "Пользователь", "Создана (UTC)", "Статус", "Категория"])
    for task in tasks:
        # Задача — пользовательский текст: апостроф предотвращает запуск формул в Excel.
        text = task["text"]
        if text.lstrip().startswith(("=", "+", "-", "@")) or text.startswith(("\t", "\r", "\n")):
            text = "'" + text
        writer.writerow([
            task["id"], text, task["user"], task["created_at"], "Новая", "Без категории"
        ])
    # BOM помогает Excel распознать UTF-8 и корректно показать кириллицу.
    return output.getvalue().encode("utf-8-sig")
