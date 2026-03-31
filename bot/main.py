import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.client.bot import DefaultBotProperties

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

# Если это версия для продашкеша, заменить "DEV" на "PROD" после знака равно
MODE: Literal["DEV", "PROD"] = "PROD"
if MODE == "DEV":
    TOKEN = cfg["SETTINGS"]["testing_token"]
    M_CHANNEL_ID = TEST_MODER_CHANNEL_ID
    REDIS_URL = cfg['CONNECTIONS']['testing_redis_url']
else:
    TOKEN = cfg["SETTINGS"]["token"]
    M_CHANNEL_ID = MODER_CHANNEL_ID
    REDIS_URL = cfg['CONNECTIONS']['redis_url']

bot = Bot(
    token=TOKEN, 
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
bot.config = cfg
bot.ADMIN_CHATS = ADMIN_CHATS
bot.MODER_CHANNEL_ID = M_CHANNEL_ID

storage = RedisStorage.from_url(url=REDIS_URL)
dp = Dispatcher(storage=storage)

# --- Подгрузка модулей ТГ бота --- #
async def main():
    logger.info("Loading modules...")

    # Создаем директорию для хранения конспектов
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
    await dp.start_polling(bot)


# --- Подгрузка базы данных --- #
async def init_db():
    await Tortoise.init(
        db_url='sqlite://bot/database/database.db',
        modules={'models': ['database.models']}
    )
    await Tortoise.generate_schemas()

if __name__ == "__main__":
    run_async(init_db())
    asyncio.run(main())
