from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from .text_on_kb import cancel, share, view


def main_kb() -> ReplyKeyboardMarkup:
    kb = [[KeyboardButton(text=share)], [KeyboardButton(text=view)]]
    return ReplyKeyboardMarkup(
        keyboard=kb, resize_keyboard=True, one_time_keyboard=True
    )


def cancel_kb() -> ReplyKeyboardMarkup:
    kb = [[KeyboardButton(text=cancel)]]
    return ReplyKeyboardMarkup(
        keyboard=kb, resize_keyboard=True, one_time_keyboard=True
    )
