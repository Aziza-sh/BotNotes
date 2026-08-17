import os
import traceback

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from elements.keybord.kb import cancel_kb, main_kb
from elements.keybord.text_on_kb import view

from elements.inline.notes_inline import create_notes_buttons
from elements.inline.note_ai import note_ai_keyboard

from elements.inline.file_inline import (
    courses_buttons_view,
    teachers_buttons_view,
    buildings_buttons_view,
    teacher_token,
)


from database.services import get_teacher_note_service, get_teachers

from database.models import Notes

router = Router()


@router.message(F.text == view)
async def view_handler(message: Message, state: FSMContext):
    try:
        await state.clear()

        await message.answer(text="✍", reply_markup=cancel_kb())

        await message.answer(
            text="Выберите учебное заведение:", reply_markup=buildings_buttons_view()
        )

    except Exception:
        traceback.print_exc()


@router.callback_query(F.data == "back_to_buildings_view")
async def back_to_buildings_handler(callback: CallbackQuery, state: FSMContext):
    try:
        await state.clear()

        await callback.message.edit_text(
            text="Выберите место обучения:", reply_markup=buildings_buttons_view()
        )

    except Exception:
        traceback.print_exc()


@router.callback_query(F.data.startswith("build_"))
async def building_selection_handler(callback: CallbackQuery, state: FSMContext):
    try:
        building_name = callback.data.split("_")[1]

        await state.update_data(building_name=building_name)

        await callback.message.edit_text(
            text="Выберите курс:",
            reply_markup=courses_buttons_view(building=building_name),
        )

    except Exception:
        traceback.print_exc()


@router.callback_query(F.data == "back_to_course_view")
async def back_to_course_handler(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()

        building_name = data.get("building_name")

        if not building_name:
            return await callback.message.edit_text(
                text=("Ошибка.\n" "Выберите место обучения заново:"),
                reply_markup=buildings_buttons_view(),
            )

        await callback.message.edit_text(
            text="Выберите курс:",
            reply_markup=courses_buttons_view(building=building_name),
        )

    except Exception:
        traceback.print_exc()


@router.callback_query(F.data.startswith("course_"))
async def course_selection_handler(callback: CallbackQuery, state: FSMContext):
    try:
        course_num = int(callback.data.split("_")[1])

        await state.update_data(course_number=course_num)

        data = await state.get_data()
        building_name = data.get("building_name")

        if not building_name:
            return await callback.message.edit_text(
                text="Ошибка состояния. Выберите учебное заведение заново:",
                reply_markup=buildings_buttons_view(),
            )

        await callback.message.edit_text(
            text="Выберите преподавателя:",
            reply_markup=await teachers_buttons_view(
                course=course_num, building=building_name, page=0
            ),
        )

    except Exception:
        traceback.print_exc()


@router.callback_query(F.data.startswith("page_"))
async def paginate_teachers_handler(callback: CallbackQuery, state: FSMContext):
    try:
        parts = callback.data.split("_")

        course_num = int(parts[1])
        page = int(parts[2])

        data = await state.get_data()
        building_name = data.get("building_name")

        await state.update_data(course_number=course_num)

        if not building_name:
            return await callback.message.edit_text(
                text="Ошибка состояния. Выберите учебное заведение заново:",
                reply_markup=buildings_buttons_view(),
            )

        await callback.message.edit_text(
            text="Выберите преподавателя:",
            reply_markup=await teachers_buttons_view(
                course=course_num, building=building_name, page=page
            ),
        )

    except Exception:
        traceback.print_exc()


@router.callback_query(F.data.startswith("t_"))
async def teacher_selection_handler(callback: CallbackQuery, state: FSMContext):
    try:
        token = callback.data[2:]

        data = await state.get_data()

        building_name = data.get("building_name")

        course_number = data.get("course_number")

        if not building_name:
            return await callback.answer("Здание не найдено", show_alert=True)

        if not course_number:
            return await callback.answer("Курс не найден", show_alert=True)

        TEACHERS = await get_teachers(
            course=int(course_number), building_name=building_name
        )

        teacher_name = next(
            (name for name in TEACHERS if teacher_token(name) == token), None
        )

        if teacher_name is None:
            return await callback.answer(
                "Список преподавателей обновился, выберите ещё раз", show_alert=True
            )

        notes = await get_teacher_note_service(
            name=teacher_name, course=int(course_number), building_name=building_name
        )

        if not notes:
            return await callback.answer(
                ("Нет одобренных " "конспектов 💔"), show_alert=True
            )

        await callback.message.edit_text(
            text=(f"Выберите конспект " f"от {teacher_name}:"),
            reply_markup=create_notes_buttons(response=notes, course=course_number),
        )

    except Exception:
        traceback.print_exc()


@router.callback_query(F.data.startswith("note_"))
async def note_selection_handler(callback: CallbackQuery):
    try:
        note_id = int(callback.data.split("_")[1])

        note = await Notes.get_or_none(id=note_id, is_deleted=False)

        if not note:
            return await callback.answer("Конспект не найден 💔", show_alert=True)

        if note.telegram_file_id:

            await callback.message.answer_document(
                document=note.telegram_file_id,
                caption=(
                    f"📄 {note.note_name}\n\n"
                    f"👨‍🏫 {note.teacher}\n"
                    f"🏫 {note.building_name}"
                ),
                reply_markup=note_ai_keyboard(note.id),
            )

        else:

            if not note.note_path:
                return await callback.answer("Файл отсутствует 💔", show_alert=True)

            if not os.path.exists(note.note_path):
                return await callback.answer(
                    ("Файл конспекта " "не найден 💔"), show_alert=True
                )

            file = FSInputFile(note.note_path)

            await callback.message.answer_document(
                document=file,
                caption=(
                    f"📄 {note.note_name}\n\n"
                    f"👨‍🏫 {note.teacher}\n"
                    f"🏫 {note.building_name}"
                ),
                reply_markup=main_kb(),
            )

    except Exception:
        traceback.print_exc()

        await callback.answer("Ошибка при открытии конспекта", show_alert=True)
