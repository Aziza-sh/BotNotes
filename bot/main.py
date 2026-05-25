import asyncio
import os
import socket
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.bot import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from typing import Literal
from tortoise import Tortoise, run_async
from loguru import logger

from config.cfg import (
    cfg, ADMIN_CHATS,
    NOTES_STORAGE_PATH,
    MODER_CHANNEL_ID,
    TEST_MODER_CHANNEL_ID
)
from events import error_handler, states_group
from handlers import commands_handler
from handlers import (
    review_notes,
    moderation,
    upload
)
from handlers.utils import mailing

MODE: Literal["DEV", "PROD"] = "DEV"
if MODE == "DEV":
    TOKEN = cfg["SETTINGS"]["testing_token"]
    M_CHANNEL_ID = TEST_MODER_CHANNEL_ID
else:
    TOKEN = cfg["SETTINGS"]["token"]
    M_CHANNEL_ID = MODER_CHANNEL_ID


# --- Автоматический поиск рабочего прокси --- #
PROXY_PORTS = [10809, 10808, 11111, 7890, 2334, 1080, 8080]

def find_proxy() -> str | None:
    for port in PROXY_PORTS:
        try:
            sock = socket.create_connection(("127.0.0.1", port), timeout=1)
            sock.close()
            logger.info(f"Найден прокси на порту {port}")
            return f"http://127.0.0.1:{port}"
        except (ConnectionRefusedError, TimeoutError, OSError):
            continue
    return None


proxy_url = find_proxy()

if proxy_url:
    session = AiohttpSession(proxy=proxy_url)
    logger.info(f"Запуск с прокси: {proxy_url}")
else:
    session = AiohttpSession()
    logger.warning("Прокси не найден — запуск без прокси")

bot = Bot(
    token=TOKEN,
    session=session,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
bot.config = cfg
bot.ADMIN_CHATS = ADMIN_CHATS
bot.MODER_CHANNEL_ID = M_CHANNEL_ID

storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# --- Подгрузка модулей ТГ бота --- #
async def main():
    logger.info("Loading modules...")
    os.makedirs(NOTES_STORAGE_PATH, exist_ok=True)
    dp.include_routers(
        error_handler.router,
        states_group.router,
        commands_handler.router,
        review_notes.router,
        upload.router,
        moderation.router,
        mailing.router
    )
    await bot.delete_webhook(drop_pending_updates=True)
    logger.success("Successfully launched")
    webhook = await bot.get_webhook_info()
    logger.info(f"Webhook: {webhook.url}")
    me = await bot.get_me()
    logger.info(f"Бот запущен как: @{me.username}")
    await dp.start_polling(bot, polling_timeout=10, handle_signals=False)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# --- Подгрузка базы данных --- #
async def init_db():
    await Tortoise.init(
        db_url=f'sqlite://{BASE_DIR}/database/database.db',
        modules={'models': ['database.models']}
    )
    await Tortoise.generate_schemas()


if __name__ == "__main__":
    run_async(init_db())
    asyncio.run(main())