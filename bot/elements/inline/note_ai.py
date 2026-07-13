from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def note_ai_keyboard(note_id: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Сгенерировать конспект",
                    callback_data=f"summary_{note_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❓ Проверочные вопросы",
                    callback_data=f"questions_{note_id}",
                )
            ],
        ]
    )

    return keyboard
