from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from elements.keybord.kb import main_kb
from elements.keybord.kb import cancel

router = Router()


class InsertText(StatesGroup):
    text = State()


class Utils(StatesGroup):
    mailing = State()


class Registration(StatesGroup):
    building_name = State()
    course_number = State()
    teacher_name = State()
    lesson_name = State()
    upload_file = State()


not_in_state_filter = ~StateFilter(
    Utils.mailing,
    InsertText.text
)


# --- Завершение заполнения формы --- #
@router.message(F.text == cancel)
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text="Запись текста прервана 🤍", 
        reply_markup=main_kb()
    )
