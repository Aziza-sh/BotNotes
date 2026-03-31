from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery
)
from aiogram.types import FSInputFile
import os
from aiogram.fsm.context import FSMContext
from elements.keybord.text_on_kb import view
from elements.inline.notes_inline import create_notes_buttons
from elements.inline.file_inline import (
    courses_buttons_view,
    teachers_buttons_view
)
from database.services import get_teacher_note_service
from database.models import Notes  

router = Router()


# Выбор курса
@router.message(F.text == view)
async def view_handler(message: Message):
    await message.answer(
        text="Выберите курс:",
        reply_markup=courses_buttons_view()
    )


# Вернуться к выбору курса
@router.callback_query(F.data == "back_to_course_view")
async def back_to_course_view_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        text="Выберите курс:",
        reply_markup=courses_buttons_view()
    )


# Выбор преподавателя из базы в зависимости от курса
@router.callback_query(F.data.startswith("course_"))
async def course_number_view(callback: CallbackQuery, state: FSMContext):
    course_num = callback.data.split("_")[1]

    await state.update_data(course_number=course_num) 
    await callback.message.edit_text(
        text="Выберите преподавателя:",
        reply_markup=await teachers_buttons_view(course=course_num, page=0)
    )


# Пагинация. (вперёд и назад). Выбор преподавателя в зависимости от курса
@router.callback_query(F.data.startswith("page_"))
async def paginate_teachers_view(callback: CallbackQuery, state: FSMContext):
    course_num = int(callback.data.split(" ")[1])
    page = int(callback.data.split(" ")[2])

    await state.update_data(course_number=course_num) 
    await callback.message.edit_text(
        text="Выберите преподавателя:",
        reply_markup=await teachers_buttons_view(course=course_num, page=page)
    )


# Выбор конспекта
@router.callback_query(F.data.startswith("t_"))
async def teacher_selection(callback: CallbackQuery, state: FSMContext):
    teacher_name = callback.data.split("_")[1]
    if len(callback.data.split("_")) > 2:
        teacher_lastname = callback.data.split("_")[2]
        teacher_name = f"{teacher_name} {teacher_lastname}"

    data = await state.get_data()
    course_number = data.get('course_number', None)
    if not course_number:
        return await callback.answer("Пожалуйста, перезагрузите панель", show_alert=True) 

    notes = await get_teacher_note_service(name=teacher_name, course=course_number)
    if not notes:
        return await callback.answer("Нет одобренных конспектов данного преподавателя 💔", show_alert=True)

    await callback.message.edit_text(
        text=f"Выберите конспект от {teacher_name}:",
        reply_markup=create_notes_buttons(response=notes, course=course_number)
    )


# Просмотр конспекта
@router.callback_query(F.data.startswith("note_"))
async def note_selection(callback: CallbackQuery):
    note_id = int(callback.data.split("_")[1])
    note = await Notes.get_or_none(id=note_id)
    if not note:
        return await callback.answer("Конспект не найден ", show_alert=True)
    
    # Проверяем существует ли файл
    if not os.path.exists(note.note_path):
       return await callback.answer("Файл конспекта не найден 💔", show_alert=True)
    
    await callback.message.edit_text(
        text=f"📄 Выбран конспект:",
        reply_markup=None
    )
        
    file = FSInputFile(note.note_path)
    await callback.message.answer_document(
        document=file,
        caption=f"Конспект: {note.note_name}"
    )
