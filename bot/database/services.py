import os
import shutil

from .models import User, Notes
from tortoise.queryset import QuerySet
from tortoise.transactions import atomic


async def get_users_service():
    users_data = await User.all()
    result = [{'user_id': entry.user_id} for entry in users_data]
    return result


@atomic()
async def get_or_create_user_service(user_id: int):
    user_data = await User.get_or_none(user_id=user_id)
    if user_data is None:
        user_data = await User.create(user_id=user_id)

    return {'user_id': user_data.user_id}


@atomic()
async def is_admin_service(user_id: int):
    user_data = await User.get_or_none(user_id=user_id)
    if not user_data:
        return {"message": "Пользователь не найден"}

    return {"status": user_data.is_admin, "message": ""}


@atomic()
async def change_admin_service(user_id: int, status: bool):
    user_data = await User.get_or_none(user_id=user_id)
    if not user_data:
        return {"message": "Пользователь не найден"}

    user_data.is_admin = status
    await user_data.save()

    return {"message": ""}


@atomic()
async def change_uploaded_notes_service(user_id: int, amount: int):
    user_data = await User.get_or_none(user_id=user_id)
    if not user_data:
        return {"message": "Пользователь не найден"}

    user_data.uploaded_notes += amount
    await user_data.save()

    return {"message": ""}


@atomic()
async def create_note_service(user_id: int, building_name:str, course: int, teacher: str, note_name: str, note_path: str):
    user_data = await User.get_or_none(user_id=user_id)
    if not user_data:
        return {"message": "Пользователь не найден"}

    note = await Notes.create(
        building_name=building_name,
        user=user_data,
        course=course,
        teacher=teacher,
        note_name=note_name,
        note_path=note_path,
        is_deleted=False  
    )
    return {"data": note, "message": ""}
      

@atomic()
async def create_note_service(user_id: int, building_name:str, course: int, teacher: str, note_name: str, note_path: str):
    user_data = await User.get_or_none(user_id=user_id)
    if not user_data:
        return {"message": "Пользователь не найден"}

    note = await Notes.create(
        building_name=building_name,
        user=user_data,
        course=course,
        teacher=teacher,
        note_name=note_name,
        note_path=note_path
    )
    note.is_deleted = True
    await note.save()
    return {"data": note, "message": ""}


async def get_notes_service():
    notes = await Notes.all()
    return [
        {
            "id": note.id,
            "is_deleted": note.is_deleted,
            "user_id": note.user_id,
            "building_name": note.building_name,
            "course": note.course,
            "teacher": note.teacher,
            "note_name": note.note_name,
            "note_path": note.note_path
        }
        for note in notes
    ]


@atomic()
async def get_teachers(course: int):
    teachers_query: QuerySet = await Notes.filter(course=course).distinct().values_list("teacher", flat=True)
    return sorted(teachers_query)  # Сортировка по алфавиту


@atomic()
async def get_teacher_note_service(name: str, course: int):
    notes = await Notes.filter(course=course, teacher=name).all()
    return [
        {
            "id": note.id,
            "is_deleted": note.is_deleted,
            "user_id": note.user_id,
            "building_name": note.building_name,
            "course": note.course,
            "teacher": note.teacher,
            "note_name": note.note_name,
            "note_path": note.note_path
        }
        for note in notes
    ]


@atomic()
async def delete_note_service(note_id: int):
    note = await Notes.get_or_none(id=note_id)
    if not note:
        return {"message": "Конспект не найден"}

    note_path = note.note_path
    if note_path and os.path.exists(note_path):
        shutil.rmtree(note_path, ignore_errors=True)

    await note.delete()
    return {"message": ""}

