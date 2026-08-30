from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def moderation_button(user_id: int, message_id: int) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Принять", callback_data=f"mod_approve_{user_id}_{message_id}"
        ),
        InlineKeyboardButton(
            text="❌ Отклонить", callback_data=f"mod_reject_{user_id}"
        ),
    )

    return builder


def teacher_moderation_button(user_id: int, course: str | int) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Добавить",
            callback_data=f"modteacher_approve_{user_id}_{course}",
        ),
        InlineKeyboardButton(
            text="❌ Отклонить", callback_data=f"modteacher_reject_{user_id}"
        ),
    )

    return builder
