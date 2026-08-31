import os

_CFG_DIR = os.path.dirname(os.path.abspath(__file__))
_BASE_DIR = os.path.dirname(_CFG_DIR)

# Читаем режим работы ("DEV" по умолчанию)
MODE: str = os.getenv("BOT_MODE", "DEV")

cfg = {
    "SETTINGS": {
        "token": os.getenv("BOT_TOKEN", "8934199632:AAELAxXXctTzvgdQspEWO4kk4nzGjkpGUoY"),
        "testing_token": os.getenv("BOT_TEST_TOKEN", "8934199632:AAELAxXXctTzvgdQspEWO4kk4nzGjkpGUoY"),
        "version": "1.0.0",
        "name": "Bot Конспекты",
    },
    "CONNECTIONS": {
        "testing_redis_url": os.getenv("TEST_REDIS_URL", "redis://localhost:6379/0"),
        "redis_url": os.getenv("REDIS_URL", "redis://localhost:6380/0"),
    },
}

API_HOST: str = "0.0.0.0"
API_PORT: int = 8000

NOTES_STORAGE_PATH: str = os.path.join(_BASE_DIR, "assets", "notes")

MODER_CHANNEL_ID: int = -1002600322209
TEST_MODER_CHANNEL_ID: int = -1002600322209
ADMIN_CHATS: list[int] = [1979132707]

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
