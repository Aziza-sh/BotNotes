import os

from config.cfg import NOTES_STORAGE_PATH
from pathlib import Path


async def save_file_to_storage(file_id: str, file_type: str, bot):
    file = await bot.get_file(file_id)
    original_ext = Path(file.file_path).suffix if file_type == "document" else ".jpg"

    file_name = f"{file_id}{original_ext}"
    file_path = os.path.join(NOTES_STORAGE_PATH, file_name)

    await bot.download_file(file.file_path, file_path)
    return file_path
