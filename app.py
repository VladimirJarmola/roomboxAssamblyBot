import asyncio
import logging
import sys
import os

from AIOHTTP import web

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application 

from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv()) #подключаем переменные окружения

from database.engine import create_db, drop_db, session_maker

from common.admin_list import admins_list

from middlewares.db import DataBaseSession

from handlers.user_private import user_private_router
from handlers.admin_private import admin_router


ALLOWED_UPDATES = ['message', 'callback_query']

bot = Bot(
    token=os.getenv('TOKEN'), 
    default=DefaultBotProperties(parse_mode=ParseMode.HTML) # включаем html разметку для всего проекта
)

bot.my_admins_list = admins_list

dp = Dispatcher()

dp.include_router(user_private_router)
dp.include_router(admin_router)

async def on_startup(dp):
    await bot.set_webhook('https://aiogram.dev/webhook') #для деплоя
    # await drop_db()

    await create_db()

async def on_shutdown(dp):
    await bot.delete_webhook()#для деплоя
    logging.error('bot not working!')

async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.update.middleware(DataBaseSession(session_pool=session_maker))
    
    await bot.delete_webhook(drop_pending_updates=True)
    # await dp.start_polling(bot, allowed_updates=ALLOWED_UPDATES)

    #для деплоя
    # Create aiohttp.web.Application instance
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path='/webhook')
    setup_application(app, dp, bot=bot)
    web.run_app(app, host=os.getenv('URL_APP'), port=5000)

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
asyncio.run(main())
