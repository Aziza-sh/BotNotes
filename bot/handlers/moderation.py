import re
import os

from aiogram import Router, F
from aiogram.types import CallbackQuery

from functions.files import save_file_to_storage
from database.services import (
    change_uploaded_notes_service,
    create_note_service
)

router = Router()


# Одобряем + заносим в БД
@router.callback_query(F.data.startswith("mod_approve_"))
async def approve_note(callback: CallbackQuery, bot):
    try:
        user_id = int(callback.data.split('_')[2])
    
        message = callback.message
        caption = message.caption

        building = re.search(r"Место обучения: (\d+)", caption).group(1)
        course = re.search(r"Курс: (\d+)", caption).group(1)
        teacher = re.search(r"Преподаватель: (.+?)\n", caption).group(1)
        note_name = re.search(r"Конспект: (.+?)(?:\n|$)", caption).group(1)

        # Получаем файл
        if message.photo:
            file_id = message.photo[-1].file_id
            file_type = "photo"
        elif message.document:
            file_id = message.document.file_id
            file_type = "document"
        else:
            return #Todo сделай сообщение

        # Сохраняем конспект
        file_path = await save_file_to_storage(file_id, file_type, bot)
        await create_note_service(
            user_id=int(user_id),
            building_name=building,
            course=int(course),
            teacher=teacher,
            note_name=note_name,
            note_path=file_path
        )

        # Обновляем счетчик
        await change_uploaded_notes_service(
            user_id=int(user_id), 
            amount=1
        )

        # Обновляем сообщение
        await message.edit_reply_markup(reply_markup=None)
        await message.reply(
            text=f"✅ Одобрено модератором {callback.from_user.username} (<code>{callback.from_user.id}</code>)"
        )

        # Уведомляем пользователя
        await bot.send_message(
            chat_id=int(user_id),
            text=f"🎉 Ваш конспект <code>{note_name}</code> был одобрен!"
        )
    except:
        await callback.answer(
            "Ошибка при обработке конспекта 💔", 
            show_alert=True
        )
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)


# Отклоняем
@router.callback_query(F.data.startswith("mod_reject_"))
async def reject_note(callback: CallbackQuery, bot):
    try:
        user_id = int(callback.data.split('_')[2])

        message = callback.message
        caption = message.caption

        note_name = re.search(r"Конспект: (.+?)(?:\n|$)", caption).group(1)

        # Обновляем сообщение
        await message.edit_reply_markup(reply_markup=None)
        await message.reply(
            text=f"❌ Отклонено модератором {callback.from_user.username} (<code>{callback.from_user.id}</code>)"
        )

        # Уведомляем пользователя
        await bot.send_message(
            chat_id=user_id,
            text=f"😕 Ваш конспект <code>{note_name}</code> был отклонен на модерации!"
        )
    except:
        await callback.answer("Ошибка при обработке", show_alert=True)
