import asyncio
import tempfile
import time
from pathlib import Path

from loguru import logger
from minio import Minio
from minio.error import S3Error

from config.cfg import (
    MINIO_ACCESS_KEY,
    MINIO_BUCKET,
    MINIO_ENDPOINT,
    MINIO_SECRET_KEY,
    MINIO_SECURE,
)

_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE,
)


def _ensure_bucket_sync(retries: int = 10, delay: float = 3.0) -> None:
    for attempt in range(1, retries + 1):
        try:
            if not _client.bucket_exists(MINIO_BUCKET):
                _client.make_bucket(MINIO_BUCKET)
                logger.success(f"Создан бакет MinIO: {MINIO_BUCKET}")
            else:
                logger.info(f"Бакет MinIO уже существует: {MINIO_BUCKET}")
            return
        except S3Error as e:
            logger.warning(f"MinIO вернул ошибку ({attempt}/{retries}): {e}")
        except Exception as e:
            logger.warning(
                f"Не удалось подключиться к MinIO ({attempt}/{retries}): {e}"
            )
        time.sleep(delay)

    logger.error(
        "Не удалось инициализировать бакет MinIO — проверьте, что сервис "
        "minio запущен и доступен по MINIO_ENDPOINT"
    )


async def ensure_bucket() -> None:
    await asyncio.to_thread(_ensure_bucket_sync)


async def upload_file(local_path: str, object_name: str) -> str:
    await asyncio.to_thread(_client.fput_object, MINIO_BUCKET, object_name, local_path)
    return object_name


async def download_to_temp(object_name: str) -> Path:
    suffix = Path(object_name).suffix
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp.close()
    await asyncio.to_thread(_client.fget_object, MINIO_BUCKET, object_name, tmp.name)
    return Path(tmp.name)


async def object_exists(object_name: str) -> bool:
    def _check() -> bool:
        try:
            _client.stat_object(MINIO_BUCKET, object_name)
            return True
        except S3Error:
            return False

    return await asyncio.to_thread(_check)


async def delete_object(object_name: str) -> None:
    try:
        await asyncio.to_thread(_client.remove_object, MINIO_BUCKET, object_name)
    except S3Error as e:
        logger.warning(f"Не удалось удалить объект {object_name} из MinIO: {e}")
