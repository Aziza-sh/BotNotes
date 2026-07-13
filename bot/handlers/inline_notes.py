from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultCachedDocument,
    InlineQueryResultCachedPhoto,
)

from database.models import Notes

router = Router()


@router.inline_query()
async def inline_notes_handler(inline_query: InlineQuery):
    query = inline_query.query.strip()
    parts = query.split()

    building: str | None = None
    course: int | None = None
    teacher: str | None = None
    note_name: str | None = None

    if len(parts) >= 1:
        building = parts[0]
    if len(parts) >= 2 and parts[1].isdigit():
        course = int(parts[1])
    if len(parts) >= 3:
        teacher = parts[2]
    if len(parts) >= 4:
        note_name = " ".join(parts[3:])

    filters: dict = {"is_deleted": False}

    if building:
        filters["building_name__icontains"] = building

    if course is not None:
        filters["course"] = course

    if teacher:
        filters["teacher__icontains"] = teacher

    queryset = Notes.filter(**filters)

    if note_name:
        queryset = queryset.filter(note_name__icontains=note_name)

    notes = await queryset.limit(50)

    results = []

    for note in notes:
        if not note.telegram_file_id:
            continue

        description = (
            f"{note.building_name} | " f"{note.course} курс | " f"{note.teacher}"
        )

        if note.telegram_file_type == "photo":
            results.append(
                InlineQueryResultCachedPhoto(
                    id=str(note.id),
                    photo_file_id=note.telegram_file_id,
                    title=note.note_name,
                    description=description,
                    caption=(
                        f"📄 {note.note_name}\n"
                        f"👨‍🏫 {note.teacher}\n"
                        f"🏫 {note.building_name}"
                    ),
                )
            )
        else:
            results.append(
                InlineQueryResultCachedDocument(
                    id=str(note.id),
                    title=note.note_name,
                    document_file_id=note.telegram_file_id,
                    description=description,
                    caption=(
                        f"📄 {note.note_name}\n"
                        f"👨‍🏫 {note.teacher}\n"
                        f"🏫 {note.building_name}"
                    ),
                )
            )

    await inline_query.answer(results=results, cache_time=1, is_personal=True)
