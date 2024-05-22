import asyncio
import logging
import sys
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommandScopeAllPrivateChats

from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv()) #подключаем переменные окружения

from handlers.user_private import user_private_router
from common.bot_cmds_list import private

ALLOWED_UPDATES = ['message']

bot = Bot(
    token=os.getenv('TOKEN'), 
    default=DefaultBotProperties(parse_mode=ParseMode.HTML) # включаем html разметку для всего проекта
)

dp = Dispatcher()

dp.include_router(user_private_router)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(commands=private, scope=BotCommandScopeAllPrivateChats())
    await dp.start_polling(bot, allowed_updates=ALLOWED_UPDATES)

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
asyncio.run(main())
