"""Учебный Telegram-бот: добавление, просмотр и экспорт личных задач."""

import asyncio
import logging
import os
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import BotCommand, BufferedInputFile, Message
from dotenv import load_dotenv

from database import add_task, get_tasks, init_db
from export_csv import make_csv

router = Router()
# Личные задачи доступны через команды только в личном чате с ботом.
router.message.filter(F.chat.type == "private")


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    """Приветствует пользователя и объясняет доступные команды."""
    await message.answer(
        "Привет! Я сохраняю твои задачи.\n\n"
        "/add Купить молоко — добавить задачу\n"
        "/list — показать свои задачи\n"
        "/list_csv — скачать свои задачи в CSV\n\n"
        "Задачи сохраняются после перезапуска бота."
    )


@router.message(Command("add"))
async def add_handler(message: Message, command: CommandObject) -> None:
    """Проверяет текст после /add и сохраняет задачу текущего пользователя."""
    text = (command.args or "").strip()
    if not text:
        await message.answer("Напиши задачу после команды. Пример: /add Купить молоко")
        return
    if len(text) > 1000:
        await message.answer("Сократи задачу до 1000 символов.")
        return
    task_id = await asyncio.to_thread(add_task, text, message.from_user.id)
    await message.answer(f"Задача №{task_id} добавлена.")


@router.message(Command("list"))
async def list_handler(message: Message) -> None:
    """Показывает личные задачи по порядку, разбивая длинный список на сообщения."""
    tasks = await asyncio.to_thread(get_tasks, message.from_user.id)
    if not tasks:
        await message.answer("Пока нет задач. Добавь первую: /add Купить молоко")
        return
    chunk = "Твои задачи:\n\n"
    for task in tasks:
        line = f"{task['id']}. {task['text']}\n"
        # Запас до лимита Telegram учитывает символы вне основной плоскости Unicode.
        if len(chunk) + len(line) > 2000:
            await message.answer(chunk)
            chunk = ""
        chunk += line
    if chunk:
        await message.answer(chunk)


@router.message(Command("list_csv"))
async def csv_handler(message: Message) -> None:
    """Отправляет CSV с личными задачами как документ в Telegram."""
    tasks = await asyncio.to_thread(get_tasks, message.from_user.id)
    if not tasks:
        await message.answer("Пока нет задач для выгрузки. Используй /add Текст задачи")
        return
    document = BufferedInputFile(make_csv(tasks), filename="tasks.csv")
    await message.answer_document(document, caption="Твои задачи в CSV. Даты указаны в UTC.")


@router.message()
async def help_handler(message: Message) -> None:
    """Подсказывает формат команд при получении неизвестной команды или сообщения."""
    await message.answer("Добавить задачу: /add Текст задачи\nСписок: /list\nCSV: /list_csv")


async def main() -> None:
    """Загружает токен, создаёт базу и запускает получение сообщений Telegram."""
    load_dotenv(Path(__file__).resolve().parent / ".env")
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token or token == "PASTE_YOUR_TOKEN_HERE":
        raise SystemExit("Добавь токен от BotFather в файл .env: BOT_TOKEN=твой_токен")
    await asyncio.to_thread(init_db)
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    # Необязательный прокси: помогает, если прямой доступ к Telegram недоступен.
    proxy_url = os.getenv("BOT_PROXY", "").strip() or None
    session = AiohttpSession(proxy=proxy_url)
    if proxy_url:
        logging.info("Подключение к Telegram через настроенный прокси")
    async with Bot(token=token, session=session) as bot:
        await bot.set_my_commands([
            BotCommand(command="start", description="Приветствие и помощь"),
            BotCommand(command="add", description="Добавить задачу: /add Текст"),
            BotCommand(command="list", description="Мои задачи"),
            BotCommand(command="list_csv", description="Скачать задачи в CSV"),
        ])
        await dispatcher.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
