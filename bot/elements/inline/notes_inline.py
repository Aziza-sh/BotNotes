from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict


def create_notes_buttons(response: List[Dict], course: int, buttons_per_row: int = 1) -> InlineKeyboardMarkup:
    keyboard = []
    for i in range(0, len(response), buttons_per_row):
        row = response[i:i + buttons_per_row]
        row_buttons = [
            InlineKeyboardButton(
                text=data['note_name'], 
                callback_data=f"note_{data['id']}"
            ) for data in row
        ]
        keyboard.append(row_buttons)

    keyboard.append([
        InlineKeyboardButton(
            text="Назад ↩️", 
            callback_data=f"course_{course}"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
