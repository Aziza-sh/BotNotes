import asyncio
import os
import socket

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger
from tortoise import Tortoise

from config.cfg import (
    ADMIN_CHATS,
    API_HOST,
    API_PORT,
    MODE,
    MODER_CHANNEL_ID,
    NOTES_STORAGE_PATH,
    TEST_MODER_CHANNEL_ID,
    cfg,
)
from events import error_handler, states_group
from handlers import (
    commands_handler,
    inline_notes,
    moderation,
    review_notes,
    upload,
    summary,
)
from handlers.utils import mailing

TOKEN = cfg["SETTINGS"]["testing_token"] if MODE == "DEV" else cfg["SETTINGS"]["token"]
M_CHANNEL = TEST_MODER_CHANNEL_ID if MODE == "DEV" else MODER_CHANNEL_ID

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── Поиск прокси
PROXY_PORTS = [10809, 10808, 11111, 7890, 2334, 1080, 8080]


def find_proxy() -> str | None:
    for port in PROXY_PORTS:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                logger.info(f"Найден прокси на порту {port}")
                return f"http://127.0.0.1:{port}"
        except OSError:
            continue
    return None


proxy_url = find_proxy()
session = AiohttpSession(proxy=proxy_url) if proxy_url else AiohttpSession()
if proxy_url:
    logger.info(f"Запуск с прокси: {proxy_url}")
else:
    logger.warning("Прокси не найден — запуск без прокси")

bot = Bot(
    token=TOKEN,
    session=session,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

bot.config = cfg
bot.ADMIN_CHATS = ADMIN_CHATS
bot.MODER_CHANNEL = M_CHANNEL

storage = MemoryStorage()
dp = Dispatcher(storage=storage)


async def init_db() -> None:
    await Tortoise.init(
        db_url=f"sqlite://{BASE_DIR}/database/database.db",
        modules={"models": ["database.models"]},
    )
    await Tortoise.generate_schemas()
    logger.success("База данных инициализирована")


async def run_bot() -> None:
    os.makedirs(NOTES_STORAGE_PATH, exist_ok=True)

    dp.include_routers(
        error_handler.router,
        states_group.router,
        commands_handler.router,
        review_notes.router,
        upload.router,
        moderation.router,
        mailing.router,
        inline_notes.router,
        summary.router,
    )

    await bot.delete_webhook(drop_pending_updates=True)

    me = await bot.get_me()
    logger.success(f"Бот запущен как @{me.username}")

    await dp.start_polling(bot, polling_timeout=10, handle_signals=False)


async def run_api() -> None:
    from api.app import app  # noqa: PLC0415

    config = uvicorn.Config(
        app=app,
        host=API_HOST,
        port=API_PORT,
        loop="none",
        log_level="info",
    )
    server = uvicorn.Server(config)
    logger.success(f"FastAPI запущен на http://{API_HOST}:{API_PORT}/docs")
    await server.serve()


async def main() -> None:
    await init_db()
    await asyncio.gather(
        run_bot(),
        run_api(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Остановлено вручную")
    finally:
        logger.info("Выход")
