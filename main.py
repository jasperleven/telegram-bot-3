#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
import sqlite3
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from aiogram import Bot, Dispatcher, executor, types

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("Не указан BOT_TOKEN!")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# --- БД ---
conn = sqlite3.connect("birthdays.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS birthdays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    name TEXT,
    date TEXT,
    note TEXT
)
""")
conn.commit()

# --- Хэндлеры ---
@dp.message_handler(commands=["start"])
def start(message: types.Message):
    message.reply("Введите дату рождения (ДД.MM):")
    dp.current_state(chat=message.chat.id).set_state("DATE")

@dp.message_handler(lambda message: dp.current_state(chat=message.chat.id).get_state() == "DATE")
def get_date(message: types.Message):
    try:
        datetime.strptime(message.text, "%d.%m")
        dp.current_state(chat=message.chat.id).update_data(date=message.text)
        message.reply("Введите имя:")
        dp.current_state(chat=message.chat.id).set_state("NAME")
    except ValueError:
        message.reply("Неверный формат. Введите ДД.MM:")

@dp.message_handler(lambda message: dp.current_state(chat=message.chat.id).get_state() == "NAME")
def get_name(message: types.Message):
    dp.current_state(chat=message.chat.id).update_data(name=message.text)
    message.reply("Введите заметку или 'нет':")
    dp.current_state(chat=message.chat.id).set_state("NOTE")

@dp.message_handler(lambda message: dp.current_state(chat=message.chat.id).get_state() == "NOTE")
def get_note(message: types.Message):
    note = message.text if message.text.lower() != "нет" else ""
    data = dp.current_state(chat=message.chat.id).get_data()
    cursor.execute(
        "INSERT INTO birthdays (chat_id, name, date, note) VALUES (?, ?, ?, ?)",
        (message.chat.id, data["name"], data["date"], note)
    )
    conn.commit()
    message.reply("Сохранено! Напоминание будет в 9:00.")
    dp.current_state(chat=message.chat.id).reset_state()

# --- Напоминания ---
def send_reminders():
    today = datetime.now().strftime("%d.%m")
    cursor.execute("SELECT chat_id, name, note FROM birthdays WHERE date=?", (today,))
    for chat_id, name, note in cursor.fetchall():
        text = f"Сегодня день рождения у {name}."
        if note:
            text += f" Примечание: {note}"
        bot.send_message(chat_id, text)

scheduler = BackgroundScheduler()
scheduler.add_job(send_reminders, 'cron', hour=9, minute=0)
scheduler.start()

# --- Запуск ---
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

