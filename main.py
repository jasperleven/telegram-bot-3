#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from dotenv import load_dotenv

# Загружаем токен
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет! Я готов к работе. Напиши /help для списка команд.")

# Команда /help
@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Список команд:\n"
        "/start - приветствие\n"
        "/help - помощь\n"
        "/info - информация о боте"
    )

# Команда /info
@dp.message(Command("info"))
async def cmd_info(message: Message):
    await message.answer("Я тестовый бот на Aiogram 3.2. Работает на Railway!")

# Ответ на любое другое сообщение
@dp.message()
async def echo_message(message: Message):
    await message.answer(f"Ты написал: {message.text}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))

