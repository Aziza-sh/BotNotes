import os
import shutil

from tortoise.queryset import QuerySet
from tortoise.transactions import atomic

from .models import User, Notes

# =========================
# USERS
# =========================


async def get_users_service():
    users_data = await User.all()

    return [{"user_id": user.user_id} for user in users_data]


@atomic()
async def get_or_create_user_service(user_id: int):

    user = await User.get_or_none(user_id=user_id)

    if not user:
        user = await User.create(user_id=user_id)

    return {"user_id": user.user_id}


@atomic()
async def is_admin_service(user_id: int):

    user = await User.get_or_none(user_id=user_id)

    if not user:
        return {"message": "Пользователь не найден"}

    return {"status": user.is_admin, "message": ""}


@atomic()
async def change_admin_service(user_id: int, status: bool):

    user = await User.get_or_none(user_id=user_id)

    if not user:
        return {"message": "Пользователь не найден"}

    user.is_admin = status

    await user.save()

    return {"message": ""}


@atomic()
async def change_uploaded_notes_service(user_id: int, amount: int):

    user = await User.get_or_none(user_id=user_id)

    if not user:
        return {"message": "Пользователь не найден"}

    user.uploaded_notes += amount

    await user.save()

    return {"message": ""}


# =========================
# NOTES
# =========================


@atomic()
async def create_note_service(
    user_id: int,
    building_name: str,
    course: int,
    teacher: str,
    note_name: str,
    note_path: str,
    telegram_file_id: str,
    telegram_file_type: str,
):

    user = await User.get_or_none(user_id=user_id)

    if not user:
        return {"message": "Пользователь не найден"}

    note = await Notes.create(
        user=user,
        building_name=building_name,
        course=course,
        teacher=teacher,
        note_name=note_name,
        note_path=note_path,
        telegram_file_id=telegram_file_id,
        telegram_file_type=telegram_file_type,
        is_deleted=False,
    )

    return {"data": note, "message": ""}


async def get_notes_service():

    notes = await Notes.filter(is_deleted=False)

    return [
        {
            "id": note.id,
            "is_deleted": note.is_deleted,
            "user_id": note.user_id,
            "building_name": note.building_name,
            "course": note.course,
            "teacher": note.teacher,
            "note_name": note.note_name,
            "note_path": note.note_path,
            "telegram_file_id": note.telegram_file_id,
        }
        for note in notes
    ]


# =========================
# TEACHERS
# =========================


@atomic()
async def get_teachers(course: int, building_name: str):

    teachers_query: QuerySet = (
        await Notes.filter(course=course, building_name=building_name, is_deleted=False)
        .distinct()
        .values_list("teacher", flat=True)
    )

    return sorted(teachers_query)


# =========================
# NOTES BY TEACHER
# =========================


@atomic()
async def get_teacher_note_service(name: str, course: int, building_name: str):

    notes = await Notes.filter(
        course=course, building_name=building_name, teacher=name, is_deleted=False
    ).all()

    return [
        {
            "id": note.id,
            "is_deleted": note.is_deleted,
            "user_id": note.user_id,
            "building_name": note.building_name,
            "course": note.course,
            "teacher": note.teacher,
            "note_name": note.note_name,
            "note_path": note.note_path,
            "telegram_file_id": note.telegram_file_id,
        }
        for note in notes
    ]


# =========================
# INLINE SEARCH
# =========================


@atomic()
async def search_notes_inline(query: str):

    parts = query.lower().split("_")

    building_name = None
    course = None
    teacher = None
    note_name = None

    if len(parts) >= 1:
        building_name = parts[0]

    if len(parts) >= 2:
        try:
            course = int(parts[1])
        except:
            course = None

    if len(parts) >= 3:
        teacher = parts[2]

    if len(parts) >= 4:
        note_name = " ".join(parts[3:])

    filters = {"is_deleted": False}

    if building_name:
        filters["building_name__icontains"] = building_name

    if course:
        filters["course"] = course

    if teacher:
        filters["teacher__icontains"] = teacher

    queryset = Notes.filter(**filters)

    if note_name:
        queryset = queryset.filter(note_name__icontains=note_name)

    return await queryset.limit(50)


# =========================
# DELETE
# =========================


@atomic()
async def delete_note_service(note_id: int):

    note = await Notes.get_or_none(id=note_id)

    if not note:
        return {"message": "Конспект не найден"}

    # Удаление файла
    if note.note_path and os.path.exists(note.note_path):

        if os.path.isfile(note.note_path):
            os.remove(note.note_path)

        elif os.path.isdir(note.note_path):
            shutil.rmtree(note.note_path, ignore_errors=True)

    await note.delete()

    return {"message": ""}
