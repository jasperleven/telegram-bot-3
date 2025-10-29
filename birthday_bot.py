#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
import sqlite3
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler

# --- Константы состояний ---
DATE, NAME, NOTE = range(3)

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

# --- Хэндлеры ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот-напоминалка о днях рождения.\nВведите дату рождения в формате ДД.MM:"
    )
    return DATE

async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    try:
        datetime.strptime(text, "%d.%m")
        context.user_data['date'] = text
        await update.message.reply_text("Введите имя человека:")
        return NAME
    except ValueError:
        await update.message.reply_text("Неверный формат. Введите дату в формате ДД.MM:")
        return DATE

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Введите дополнительную информацию (или 'нет'):")
    return NOTE

async def get_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    note = update.message.text
    if note.lower() == "нет":
        note = ""
    context.user_data['note'] = note

    cursor.execute(
        "INSERT INTO birthdays (user_id, name, date, note) VALUES (?, ?, ?, ?)",
        (update.message.chat_id, context.user_data['name'], context.user_data['date'], note)
    )
    conn.commit()

    await update.message.reply_text("Записано! Я буду напоминать о дне рождения в 9:00.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отмена.")
    return ConversationHandler.END

# --- Функция напоминания ---
async def send_birthday_reminder(app):
    today = datetime.now().strftime("%d.%m")
    cursor.execute("SELECT user_id, name, note FROM birthdays WHERE date=?", (today,))
    rows = cursor.fetchall()
    for user_id, name, note in rows:
        message = f"Сегодня день рождения у {name}."
        if note:
            message += f" Примечание: {note}"
        await app.bot.send_message(chat_id=user_id, text=message)

# --- Планировщик ---
def start_scheduler(app):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: send_birthday_reminder(app), 'cron', hour=9, minute=0)
    scheduler.start()

# --- Основной запуск ---
if __name__ == "__main__":
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("Не указан BOT_TOKEN в переменных окружения!")

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_note)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(conv_handler)

    start_scheduler(app)

    app.run_polling()

