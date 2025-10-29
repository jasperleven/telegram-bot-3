#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
import sqlite3
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

# --- Подключение к базе данных ---
conn = sqlite3.connect("birthdays.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS birthdays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT,
    date TEXT,
    note TEXT
)
""")
conn.commit()

# --- FSM состояния ---
class BirthdayForm(StatesGroup):
    date = State()
    name = State()
    note = State()

# --- Инициализация бота ---
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("Не указан BOT_TOKEN в переменных окружения!")

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- Хэндлеры ---
@dp.message_handler(commands="start")
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я бот-напоминалка о днях рождения.\nВведите дату рождения в формате ДД.MM:")
    await BirthdayForm.date.set()

@dp.message_handler(state=BirthdayForm.date)
async def process_date(message: types.Message, state: FSMContext):
    text = message.text
    try:
        datetime.strptime(text, "%d.%m")
        await state.update_data(date=text)
        await message.answer("Введите имя человека:")
        await BirthdayForm.next()
    except ValueError:
        await message.answer("Неверный формат. Введите дату в формате ДД.MM:")

@dp.message_handler(state=BirthdayForm.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите дополнительную информацию (или 'нет'):")
    await BirthdayForm.next()

@dp.message_handler(state=BirthdayForm.note)
async def process_note(message: types.Message, state: FSMContext):
    note = message.text
    if note.lower() == "нет":
        note = ""
    data = await state.get_data()
    cursor.execute(
        "INSERT INTO birthdays (user_id, name, date, note) VALUES (?, ?, ?, ?)",
        (message.chat.id, data['name'], data['date'], note)
    )
    conn.commit()
    await message.answer("Записано! Я буду напоминать о дне рождения в 9:00.")
    await state.finish()

# --- Функция напоминания ---
async def send_birthday_reminder():
    today = datetime.now().strftime("%d.%m")
    cursor.execute("SELECT user_id, name, note FROM birthdays WHERE date=?", (today,))
    rows = cursor.fetchall()
    for user_id, name, note in rows:
        text = f"Сегодня день рождения у {name}."
        if note:
            text += f" Примечание: {note}"
        await bot.send_message(chat_id=user_id, text=text)

# --- Планировщик ---
scheduler = AsyncIOScheduler()
scheduler.add_job(send_birthday_reminder, 'cron', hour=9, minute=0)
scheduler.start()

# --- Запуск ---
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

