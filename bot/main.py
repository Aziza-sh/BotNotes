import asyncio
import os

import uvicorn
from loguru import logger
from tortoise import Tortoise

from config.cfg import API_HOST, API_PORT
from events import error_handler, states_group
from functions.storage import ensure_bucket
from handlers import (
    commands_handler,
    inline_notes,
    moderation,
    review_notes,
    upload,
)
from handlers.utils import mailing

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_DIR = os.path.join(BASE_DIR, "storage")
DB_PATH = os.path.join(DB_DIR, "database.db")

# Какую роль играет этот процесс/контейнер:
#   "all" — бот + API в одном процессе (по умолчанию, для локальной разработки)
#   "bot" — только Telegram-бот (aiogram polling)
#   "api" — только REST API (uvicorn)
SERVICE_ROLE = os.getenv("SERVICE_ROLE", "all").strip().lower()


async def init_db() -> None:
    os.makedirs(DB_DIR, exist_ok=True)
    await Tortoise.init(
        db_url=f"sqlite://{DB_PATH}",
        modules={"models": ["database.models"]},
    )
    await Tortoise.generate_schemas()
    logger.success("База данных инициализирована")


def build_bot_and_dispatcher():
    from aiogram import Bot, Dispatcher
    from aiogram.client.bot import DefaultBotProperties
    from aiogram.client.session.aiohttp import AiohttpSession
    from aiogram.enums import ParseMode
    from aiogram.fsm.storage.memory import MemoryStorage

    from config.cfg import (
        ADMIN_CHATS,
        MODE,
        MODER_CHANNEL_ID,
        TEST_MODER_CHANNEL_ID,
        cfg,
    )

    token = (
        cfg["SETTINGS"]["testing_token"] if MODE == "DEV" else cfg["SETTINGS"]["token"]
    )
    m_channel = TEST_MODER_CHANNEL_ID if MODE == "DEV" else MODER_CHANNEL_ID

    bot = Bot(
        token=token,
        session=AiohttpSession(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    bot.config = cfg
    bot.ADMIN_CHATS = ADMIN_CHATS
    bot.MODER_CHANNEL = m_channel

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    return bot, dp


async def run_bot() -> None:
    bot, dp = build_bot_and_dispatcher()

    dp.include_routers(
        error_handler.router,
        states_group.router,
        commands_handler.router,
        review_notes.router,
        upload.router,
        moderation.router,
        mailing.router,
        inline_notes.router,
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
    await ensure_bucket()

    if SERVICE_ROLE == "bot":
        logger.info("Роль сервиса: только бот")
        await run_bot()
    elif SERVICE_ROLE == "api":
        logger.info("Роль сервиса: только API")
        await run_api()
    else:
        logger.info("Роль сервиса: бот + API в одном процессе")
        await asyncio.gather(run_bot(), run_api())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Остановлено вручную")
    finally:
        logger.info("Выход")
