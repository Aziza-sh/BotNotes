import os
import tempfile
from pathlib import Path

from functions.storage import upload_file


async def save_file_to_storage(file_id: str, file_type: str, bot) -> str:
    file = await bot.get_file(file_id)
    original_ext = Path(file.file_path).suffix if file_type == "document" else ".jpg"

    object_name = f"notes/{file_id}{original_ext}"

    tmp = tempfile.NamedTemporaryFile(suffix=original_ext, delete=False)
    tmp.close()

    try:
        await bot.download_file(file.file_path, tmp.name)
        await upload_file(tmp.name, object_name)
    finally:
        os.remove(tmp.name)

    return object_name
