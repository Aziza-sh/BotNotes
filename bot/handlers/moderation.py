import re
import os
import traceback

from aiogram import Router, F
from aiogram.types import CallbackQuery

from functions.files import save_file_to_storage
from database.services import change_uploaded_notes_service, create_note_service

router = Router()


# Одобряем + заносим в БД
@router.callback_query(F.data.startswith("mod_approve_"))
async def approve_note(callback: CallbackQuery, bot):
    try:
        user_id = int(callback.data.split("_")[2])

        message = callback.message
        caption = message.caption

        if not caption:
            return await callback.answer("Caption отсутствует", show_alert=True)

        building_match = re.search(r"Учебное заведение: (.+?)\n", caption)

        course_match = re.search(r"Курс: (.+?)\n", caption)

        teacher_match = re.search(r"Преподаватель: (.+?)\n", caption)

        note_match = re.search(r"Конспект: (.+?)(?:\n|$)", caption)

        if not all([building_match, course_match, teacher_match, note_match]):
            return await callback.answer(
                "Ошибка чтения данных конспекта", show_alert=True
            )

        building = building_match.group(1)
        course = course_match.group(1)
        teacher = teacher_match.group(1)
        note_name = note_match.group(1)

        # Получаем файл
        if message.photo:
            file_id = message.photo[-1].file_id
            file_type = "photo"

        elif message.document:
            file_id = message.document.file_id
            file_type = "document"

        else:
            return await callback.answer("Файл не найден", show_alert=True)

        # Сохраняем файл
        file_path = await save_file_to_storage(
            file_id=file_id, file_type=file_type, bot=bot
        )

        # Создаем запись
        await create_note_service(
            user_id=user_id,
            building_name=building,
            course=int(course),
            teacher=teacher,
            note_name=note_name,
            note_path=file_path,
            telegram_file_id=file_id,
            telegram_file_type=file_type,
        )

        # Обновляем счетчик
        await change_uploaded_notes_service(user_id=user_id, amount=1)

        # Убираем кнопки
        await message.edit_reply_markup(reply_markup=None)

        # Сообщение в модерацию
        await bot.send_message(
            chat_id=message.chat.id,
            text=(
                f"✅ Одобрено модератором "
                f"{callback.from_user.username} "
                f"(<code>{callback.from_user.id}</code>)"
            ),
        )

        # Уведомляем пользователя
        await bot.send_message(
            chat_id=user_id,
            text=(f"🎉 Ваш конспект " f"<code>{note_name}</code> " f"был одобрен!"),
        )

    except Exception as e:
        traceback.print_exc()

        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)

        if "file_path" in locals():
            if os.path.exists(file_path):
                os.remove(file_path)


# Отклоняем
@router.callback_query(F.data.startswith("mod_reject_"))
async def reject_note(callback: CallbackQuery, bot):
    try:
        user_id = int(callback.data.split("_")[2])

        message = callback.message
        caption = message.caption

        note_match = re.search(r"Конспект: (.+?)(?:\n|$)", caption)

        note_name = note_match.group(1) if note_match else "Без названия"

        # Убираем кнопки
        await message.edit_reply_markup(reply_markup=None)

        # Сообщение в модерацию
        await bot.send_message(
            chat_id=message.chat.id,
            text=(
                f"❌ Отклонено модератором "
                f"{callback.from_user.username} "
                f"(<code>{callback.from_user.id}</code>)"
            ),
        )

        # Уведомляем пользователя
        await bot.send_message(
            chat_id=user_id,
            text=(f"😕 Ваш конспект " f"<code>{note_name}</code> " f"был отклонен!"),
        )

    except Exception as e:
        traceback.print_exc()

        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)
