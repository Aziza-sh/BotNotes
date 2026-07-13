import tempfile
import traceback
from pathlib import Path

from aiogram import F, Router
from aiogram.types import CallbackQuery, FSInputFile

from ai.lecture_processor import (
    summarize_file,
    get_questions,
)

from database.services import get_note_by_id_service

router = Router()

MAX_MESSAGE_LENGTH = 4000


async def get_note_file(note_id: int):

    note = await get_note_by_id_service(note_id)

    if note is None:
        return None, "Конспект не найден 💔"

    if not note.note_path:
        return None, "Файл отсутствует 💔"

    file_path = Path(note.note_path)

    if not file_path.exists():
        return None, "Файл не найден 💔"

    return file_path, None


@router.callback_query(F.data.startswith("summary_"))
async def summary_handler(callback: CallbackQuery):

    try:

        note_id = int(callback.data.split("_")[1])

        file_path, error = await get_note_file(note_id)

        if error:
            return await callback.answer(error, show_alert=True)

        await callback.answer()

        wait = await callback.message.answer(
            "⏳ Генерирую конспект...\n\n" "Это может занять несколько минут."
        )

        summary = summarize_file(file_path)

        await wait.edit_text("✅ Конспект готов!")

        if len(summary) <= MAX_MESSAGE_LENGTH:

            await callback.message.answer(summary)

            return

        with tempfile.NamedTemporaryFile(
            suffix=".md",
            delete=False,
            mode="w",
            encoding="utf-8",
        ) as tmp:

            tmp.write(summary)
            temp_path = Path(tmp.name)

        await callback.message.answer_document(
            FSInputFile(temp_path),
            caption="📝 AI-конспект",
        )

        temp_path.unlink(missing_ok=True)

    except Exception:

        traceback.print_exc()

        await callback.message.answer("❌ Ошибка при генерации конспекта.")


@router.callback_query(F.data.startswith("questions_"))
async def questions_handler(callback: CallbackQuery):

    try:

        note_id = int(callback.data.split("_")[1])

        file_path, error = await get_note_file(note_id)

        if error:
            return await callback.answer(error, show_alert=True)

        await callback.answer()

        wait = await callback.message.answer("⏳ Генерирую проверочные вопросы...")

        questions = get_questions(file_path)

        if not questions:

            await wait.edit_text("❌ Не удалось сгенерировать вопросы.")

            return

        questions_text = "\n".join(
            f"{index}. {question}" for index, question in enumerate(questions, start=1)
        )

        await wait.edit_text("✅ Вопросы готовы!")

        if len(questions_text) <= MAX_MESSAGE_LENGTH:

            await callback.message.answer(questions_text)

            return

        with tempfile.NamedTemporaryFile(
            suffix=".md",
            delete=False,
            mode="w",
            encoding="utf-8",
        ) as tmp:

            tmp.write(questions_text)
            temp_path = Path(tmp.name)

        await callback.message.answer_document(
            FSInputFile(temp_path),
            caption="❓ Проверочные вопросы",
        )

        temp_path.unlink(missing_ok=True)

    except Exception:

        traceback.print_exc()

        await callback.message.answer("❌ Ошибка при генерации вопросов.")
