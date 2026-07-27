import os
import shutil

from tortoise.transactions import atomic

from .models import User, Notes, CustomTeacher


async def get_users_service() -> list[dict]:

    users = await User.all()
    return [{"user_id": u.user_id} for u in users]


@atomic()
async def get_or_create_user_service(user_id: int) -> dict:

    user, _ = await User.get_or_create(user_id=user_id)
    return {"user_id": user.user_id}


@atomic()
async def is_admin_service(user_id: int) -> dict:

    user = await User.get_or_none(user_id=user_id)
    if not user:
        return {"message": "Пользователь не найден"}
    return {"status": user.is_admin, "message": ""}


@atomic()
async def change_admin_service(user_id: int, status: bool) -> dict:

    user = await User.get_or_none(user_id=user_id)
    if not user:
        return {"message": "Пользователь не найден"}
    user.is_admin = status
    await user.save()
    return {"message": ""}


@atomic()
async def change_uploaded_notes_service(user_id: int, amount: int) -> dict:

    user = await User.get_or_none(user_id=user_id)
    if not user:
        return {"message": "Пользователь не найден"}
    user.uploaded_notes += amount
    await user.save()
    return {"message": ""}


@atomic()
async def get_user_statistic_service(user_id: int) -> dict:

    user = await User.get_or_none(user_id=user_id)
    if not user:
        return {"message": "Пользователь не найден"}
    return {
        "uploaded_notes": user.uploaded_notes,
        "message": "",
    }


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
) -> dict:

    user, _ = await User.get_or_create(user_id=user_id)

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
    return {"data": note, "telegram_user_id": user.user_id, "message": ""}


async def get_notes_service() -> list[dict]:

    notes = await Notes.filter(is_deleted=False).select_related("user")
    return [_note_to_dict(n) for n in notes]


@atomic()
async def get_teachers(course: int, building_name: str | None = None) -> list[str]:
    """Раньше принимала только course, но вызывалась ещё и с building_name
    (elements/inline/file_inline.py -> teachers_buttons_view), из-за чего
    падала с TypeError и экран "Просмотр конспектов" молча ломался.
    Теперь building_name — опциональный фильтр, старые вызовы с одним
    course (см. api/routers/notes.py) продолжают работать как раньше.
    """
    filters: dict = {"course": course, "is_deleted": False}
    if building_name:
        filters["building_name"] = building_name

    result: list[str] = (
        await Notes.filter(**filters).distinct().values_list("teacher", flat=True)
    )
    return sorted(result)


@atomic()
async def get_custom_teachers_service(course: int) -> list[str]:

    result: list[str] = (
        await CustomTeacher.filter(course=course, is_deleted=False)
        .distinct()
        .values_list("full_name", flat=True)
    )
    return sorted(result)


@atomic()
async def add_custom_teacher_service(course: int, full_name: str) -> dict:

    existing = await CustomTeacher.get_or_none(
        course=course, full_name=full_name, is_deleted=False
    )
    if existing:
        return {"data": existing, "message": ""}

    teacher = await CustomTeacher.create(course=course, full_name=full_name)
    return {"data": teacher, "message": ""}


@atomic()
async def get_teacher_note_service(
    name: str,
    course: int,
    building_name: str,
) -> list[dict]:

    notes = await Notes.filter(
        course=course,
        building_name=building_name,
        teacher=name,
        is_deleted=False,
    ).select_related("user")
    return [_note_to_dict(n) for n in notes]


@atomic()
async def search_notes_inline(query: str):

    parts = query.split("_")

    building_name = parts[0] if len(parts) >= 1 and parts[0] else None
    course = int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else None
    teacher = parts[2] if len(parts) >= 3 and parts[2] else None
    note_name = " ".join(parts[3:]) if len(parts) >= 4 else None

    filters: dict = {"is_deleted": False}
    if building_name:
        filters["building_name__icontains"] = building_name
    if course:
        filters["course"] = course
    if teacher:
        filters["teacher__icontains"] = teacher

    qs = Notes.filter(**filters)
    if note_name:
        qs = qs.filter(note_name__icontains=note_name)

    return await qs.limit(50)


@atomic()
async def delete_note_service(note_id: int) -> dict:

    note = await Notes.get_or_none(id=note_id)
    if not note:
        return {"message": "Конспект не найден"}

    if note.note_path and os.path.exists(note.note_path):
        if os.path.isfile(note.note_path):
            os.remove(note.note_path)
        elif os.path.isdir(note.note_path):
            shutil.rmtree(note.note_path, ignore_errors=True)

    await note.delete()
    return {"message": ""}


def _note_to_dict(note: Notes) -> dict:

    return {
        "id": note.id,
        "is_deleted": note.is_deleted,
        "user_id": note.user.user_id,
        "building_name": note.building_name,
        "course": note.course,
        "teacher": note.teacher,
        "note_name": note.note_name,
        "note_path": note.note_path,
        "telegram_file_id": note.telegram_file_id,
        "telegram_file_type": note.telegram_file_type,
    }


@atomic()
async def get_note_by_id_service(note_id: int) -> Notes | None:

    return await Notes.get_or_none(
        id=note_id,
        is_deleted=False,
    )
