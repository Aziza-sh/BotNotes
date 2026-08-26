import re
import traceback

from aiogram import Router, F
from aiogram.types import CallbackQuery

from functions.files import save_file_to_storage
from functions.storage import delete_object
from database.services import (
    change_uploaded_notes_service,
    create_note_service,
    add_custom_teacher_service,
)

router = Router()


# Одобряем + заносим в БД


@router.callback_query(F.data.startswith("mod_approve_"))
async def approve_note(callback: CallbackQuery, bot):
    if callback.from_user.id not in bot.ADMIN_CHATS:
        return await callback.answer("Нет прав", show_alert=True)

    try:
        parts = callback.data.split("_")
        user_id = int(parts[2])

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
                "Ошибка чтения данных конспекта из подписи", show_alert=True
            )

        building = building_match.group(1).strip()
        course = course_match.group(1).strip()
        teacher = teacher_match.group(1).strip()
        note_name = note_match.group(1).strip()

        if message.photo:
            file_id = message.photo[-1].file_id
            file_type = "photo"
        elif message.document:
            file_id = message.document.file_id
            file_type = "document"
        else:
            return await callback.answer("Файл не найден в сообщении", show_alert=True)

        file_path = await save_file_to_storage(
            file_id=file_id, file_type=file_type, bot=bot
        )

        result = await create_note_service(
            user_id=user_id,
            building_name=building,
            course=int(course),
            teacher=teacher,
            note_name=note_name,
            note_path=file_path,
            telegram_file_id=file_id,
            telegram_file_type=file_type,
        )

        if result.get("message"):
            return await callback.answer(
                f"Ошибка сохранения: {result['message']}", show_alert=True
            )

        await change_uploaded_notes_service(user_id=user_id, amount=1)

        await message.edit_reply_markup(reply_markup=None)

        await bot.send_message(
            chat_id=message.chat.id,
            text=(
                f"✅ Одобрено модератором "
                f"@{callback.from_user.username or callback.from_user.id} "
                f"(<code>{callback.from_user.id}</code>)"
            ),
        )

        await bot.send_message(
            chat_id=user_id,
            text=f"🎉 Ваш конспект <code>{note_name}</code> был одобрен!",
        )

    except Exception as e:
        traceback.print_exc()

        if "file_path" in locals():
            await delete_object(file_path)

        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)


# Отклоняем


@router.callback_query(F.data.startswith("mod_reject_"))
async def reject_note(callback: CallbackQuery, bot):
    if callback.from_user.id not in bot.ADMIN_CHATS:
        return await callback.answer("Нет прав", show_alert=True)

    try:
        user_id = int(callback.data.split("_")[2])

        message = callback.message
        caption = message.caption

        note_match = re.search(r"Конспект: (.+?)(?:\n|$)", caption) if caption else None
        note_name = note_match.group(1).strip() if note_match else "Без названия"

        await message.edit_reply_markup(reply_markup=None)

        await bot.send_message(
            chat_id=message.chat.id,
            text=(
                f"❌ Отклонено модератором "
                f"@{callback.from_user.username or callback.from_user.id} "
                f"(<code>{callback.from_user.id}</code>)"
            ),
        )

        await bot.send_message(
            chat_id=user_id,
            text=f"😕 Ваш конспект <code>{note_name}</code> был отклонён.",
        )

    except Exception as e:
        traceback.print_exc()
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)


# Одобряем добавление преподавателя + заносим в БД


@router.callback_query(F.data.startswith("modteacher_approve_"))
async def approve_teacher(callback: CallbackQuery, bot):
    if callback.from_user.id not in bot.ADMIN_CHATS:
        return await callback.answer("Нет прав", show_alert=True)

    try:
        parts = callback.data.split("_")
        user_id = int(parts[2])
        course = int(parts[3])

        message = callback.message
        text = message.text

        if not text:
            return await callback.answer("Текст заявки отсутствует", show_alert=True)

        teacher_match = re.search(r"ФИО: (.+?)(?:\n|$)", text)

        if not teacher_match:
            return await callback.answer("Ошибка чтения ФИО из заявки", show_alert=True)

        full_name = teacher_match.group(1).strip()

        result = await add_custom_teacher_service(course=course, full_name=full_name)

        if result.get("message"):
            return await callback.answer(
                f"Ошибка сохранения: {result['message']}", show_alert=True
            )

        await message.edit_reply_markup(reply_markup=None)

        await bot.send_message(
            chat_id=message.chat.id,
            text=(
                f"✅ Преподаватель добавлен модератором "
                f"@{callback.from_user.username or callback.from_user.id} "
                f"(<code>{callback.from_user.id}</code>)"
            ),
        )

        await bot.send_message(
            chat_id=user_id,
            text=(
                f"🎉 Преподаватель <code>{full_name}</code> добавлен в список "
                f"для {course} курса!"
            ),
        )

    except Exception as e:
        traceback.print_exc()
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)


# Отклоняем добавление преподавателя


@router.callback_query(F.data.startswith("modteacher_reject_"))
async def reject_teacher(callback: CallbackQuery, bot):
    if callback.from_user.id not in bot.ADMIN_CHATS:
        return await callback.answer("Нет прав", show_alert=True)

    try:
        user_id = int(callback.data.split("_")[2])

        message = callback.message
        text = message.text

        teacher_match = re.search(r"ФИО: (.+?)(?:\n|$)", text) if text else None
        full_name = teacher_match.group(1).strip() if teacher_match else "неизвестно"

        await message.edit_reply_markup(reply_markup=None)

        await bot.send_message(
            chat_id=message.chat.id,
            text=(
                f"❌ Заявка отклонена модератором "
                f"@{callback.from_user.username or callback.from_user.id} "
                f"(<code>{callback.from_user.id}</code>)"
            ),
        )

        await bot.send_message(
            chat_id=user_id,
            text=(
                f"😕 Заявка на добавление преподавателя <code>{full_name}</code> "
                f"была отклонена."
            ),
        )

    except Exception as e:
        traceback.print_exc()
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)
