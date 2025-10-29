#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
import sqlite3
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

# --- Состояния ---
DATE, NAME, NOTE = range(3)

# --- База данных ---
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

# --- Хэндлеры ---
def start(update, context):
    update.message.reply_text("Привет! Введите дату рождения (ДД.MM):")
    return DATE

def get_date(update, context):
    try:
        datetime.strptime(update.message.text, "%d.%m")
        context.user_data['date'] = update.message.text
        update.message.reply_text("Введите имя человека:")
        return NAME
    except ValueError:
        update.message.reply_text("Неверный формат. Введите ДД.MM:")
        return DATE

def get_name(update, context):
    context.user_data['name'] = update.message.text
    update.message.reply_text("Введите дополнительную информацию (или 'нет'):")
    return NOTE

def get_note(update, context):
    note = update.message.text
    if note.lower() == "нет":
        note = ""
    context.user_data['note'] = note

    cursor.execute(
        "INSERT INTO birthdays (user_id, name, date, note) VALUES (?, ?, ?, ?)",
        (update.message.chat_id, context.user_data['name'], context.user_data['date'], note)
    )
    conn.commit()
    update.message.reply_text("Записано! Напоминание будет в 9:00.")
    return ConversationHandler.END

def cancel(update, context):
    update.message.reply_text("Отмена.")
    return ConversationHandler.END

# --- Напоминания ---
def send_reminder(bot):
    today = datetime.now().strftime("%d.%m")
    cursor.execute("SELECT user_id, name, note FROM birthdays WHERE date=?", (today,))
    rows = cursor.fetchall()
    for user_id, name, note in rows:
        text = f"Сегодня день рождения у {name}."
        if note:
            text += f" Примечание: {note}"
        bot.send_message(chat_id=user_id, text=text)

def start_scheduler(updater):
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: send_reminder(updater.bot), 'cron', hour=9, minute=0)
    scheduler.start()

# --- Основной запуск ---
if __name__ == "__main__":
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("Не указан BOT_TOKEN в переменных окружения!")

    updater = Updater(TOKEN)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            DATE: [MessageHandler(Filters.text & ~Filters.command, get_date)],
            NAME: [MessageHandler(Filters.text & ~Filters.command, get_name)],
            NOTE: [MessageHandler(Filters.text & ~Filters.command, get_note)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)

    start_scheduler(updater)

    updater.start_polling()
    updater.idle()

