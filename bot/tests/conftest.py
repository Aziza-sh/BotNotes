"""
Общие фикстуры для тестов.

Важный момент: bot/config/cfg.py в .gitignore и в репозитории физически
не существует — там лежат реальные токены/секреты. Поэтому перед тем как
что-либо импортировать из bot/ (main.py, functions.storage, database.services
и т.д. — они все транзитивно тянут `from config.cfg import ...`), мы
подсовываем в sys.modules фиктивный модуль config.cfg с безопасными
заглушками. Реальные сетевые вызовы (Telegram, MinIO) в тестах не
выполняются — только конструирование объектов.
"""

import sys
import types
from pathlib import Path

import pytest
from tortoise import Tortoise

BOT_DIR = Path(__file__).resolve().parent.parent
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))


def _install_fake_config() -> None:
    if "config.cfg" in sys.modules:
        return

    fake_cfg_module = types.ModuleType("config.cfg")
    fake_cfg_module.cfg = {
        "SETTINGS": {
            "token": "TEST:TOKEN",
            "testing_token": "TEST:TOKEN",
        }
    }
    fake_cfg_module.MODE = "DEV"
    fake_cfg_module.ADMIN_CHATS = [123456789]
    fake_cfg_module.MODER_CHANNEL_ID = -1001111111111
    fake_cfg_module.TEST_MODER_CHANNEL_ID = -1002222222222
    fake_cfg_module.API_HOST = "127.0.0.1"
    fake_cfg_module.API_PORT = 8000
    fake_cfg_module.MINIO_ENDPOINT = "127.0.0.1:9000"
    fake_cfg_module.MINIO_ACCESS_KEY = "test-access-key"
    fake_cfg_module.MINIO_SECRET_KEY = "test-secret-key"
    fake_cfg_module.MINIO_BUCKET = "test-bucket"
    fake_cfg_module.MINIO_SECURE = False

    # config/__init__.py существует в репозитории и реален — не подменяем
    # его, но родительский пакет обязан быть импортируемым до дочернего.
    import config  # noqa: F401  (реальный пакет bot/config)

    sys.modules["config.cfg"] = fake_cfg_module
    sys.modules["config"].cfg_module = fake_cfg_module


_install_fake_config()


@pytest.fixture(autouse=True)
async def tortoise_db():
    """
    Чистая in-memory SQLite база на каждый тест — быстро и без побочных
    эффектов между тестами.
    """
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": ["database.models"]},
    )
    await Tortoise.generate_schemas()
    try:
        yield
    finally:
        await Tortoise.close_connections()


@pytest.fixture
def anyio_backend():
    return "asyncio"
