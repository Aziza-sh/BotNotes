import re

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from elements.inline.moderation_inline import moderation_button
from elements.keybord.kb import cancel_kb
from elements.keybord.text_on_kb import share

from events.states_group import Registration

from elements.inline.file_inline import (
    buildings_buttons,
    courses_buttons,
    teachers_buttons,
)

router = Router()


@router.message(F.text == share)
async def start_share_handler(message: Message, state: FSMContext):
    await message.answer(text="✍", reply_markup=cancel_kb())
    await message.answer(
        text="Выберите учебное заведение:", reply_markup=buildings_buttons()
    )
    await state.set_state(Registration.building_name)


@router.callback_query(F.data.startswith("build "))
async def building_select_handler(callback: CallbackQuery, state: FSMContext):
    building = callback.data.split(" ")[1]
    await state.update_data(building=building)
    await callback.message.edit_text(
        text="Выберите курс:", reply_markup=courses_buttons()
    )
    await state.set_state(Registration.course_number)


@router.callback_query(F.data == "back_to_building")
async def back_to_building_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Выберите учебное заведение:", reply_markup=buildings_buttons()
    )
    await state.set_state(Registration.building_name)


@router.callback_query(F.data == "back_to_course")
async def back_to_course_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Выберите курс:", reply_markup=courses_buttons()
    )
    await state.set_state(Registration.course_number)


@router.callback_query(F.data.startswith("course "))
async def course_select_handler(callback: CallbackQuery, state: FSMContext):
    course_num = callback.data.split(" ")[1]
    await state.update_data(course_number=course_num)
    await callback.message.edit_text(
        text="Выберите преподавателя:",
        reply_markup=teachers_buttons(course=course_num, page=0),
    )
    await state.set_state(Registration.teacher_name)


@router.callback_query(F.data.startswith("page "))
async def teachers_pagination_handler(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(" ")
    course_num = int(parts[1])
    page = int(parts[2])
    await state.update_data(course_number=course_num)
    await callback.message.edit_text(
        text="Выберите преподавателя:",
        reply_markup=teachers_buttons(course=course_num, page=page),
    )


@router.callback_query(F.data.startswith("t "))
async def teacher_select_handler(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(" ")
    teacher_name = " ".join(parts[1:])
    await state.update_data(teacher_name=teacher_name)
    await callback.message.edit_text(
        text="Напишите название конспекта (10-150 символов):", reply_markup=None
    )
    await state.set_state(Registration.lesson_name)


@router.message(Registration.lesson_name, F.text)
async def lesson_name_handler(message: Message, state: FSMContext):
    lesson_name = re.sub(r"[<>]", "", message.text[:150])
    if len(lesson_name) < 10:
        return await message.answer("Название должно быть от 10 до 150 символов")
    await state.update_data(lesson_name=lesson_name)
    await message.answer(text="Отправьте конспект (фото или документ):")
    await state.set_state(Registration.upload_file)


@router.message(Registration.upload_file)
async def upload_file_handler(message: Message, state: FSMContext, bot):
    data = await state.get_data()

    caption = (
        f"🏫 Учебное заведение: {data.get('building')}\n"
        f"📚 Курс: {data.get('course_number')}\n"
        f"👨‍🏫 Преподаватель: {data.get('teacher_name')}\n"
        f"📝 Конспект: {data.get('lesson_name')}\n"
        f"👤 Пользователь: @{message.from_user.username or 'отсутствует'} "
        f"(<code>{message.from_user.id}</code>)"
    )

    if message.photo:
        await bot.send_photo(
            chat_id=bot.MODER_CHANNEL,
            photo=message.photo[-1].file_id,
            caption=caption,
            reply_markup=moderation_button(
                user_id=message.from_user.id, message_id=message.message_id
            ).as_markup(),
        )

    elif message.document:
        await bot.send_document(
            chat_id=bot.MODER_CHANNEL,
            document=message.document.file_id,
            caption=caption,
            reply_markup=moderation_button(
                user_id=message.from_user.id, message_id=message.message_id
            ).as_markup(),
        )

    else:
        return await message.answer("Отправьте фото или документ")

    await message.answer(
        text="Конспект отправлен на модерацию!", reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()
