#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()  # Загружает токен из .env

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Не найден BOT_TOKEN в .env")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer("Бот работает! 🚀")

@dp.message()
async def echo(message: Message):
    await message.answer(f"Вы написали: {message.text}")

if __name__ == "__main__":
    import asyncio
    from aiogram import F
    from aiogram.types import BotCommand
    from aiogram import executor

    async def main():
        await bot.set_my_commands([BotCommand(command="start", description="Запустить бота")])
        await dp.start_polling(bot)

    asyncio.run(main())

