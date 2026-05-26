import traceback

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
    try:

        query = inline_query.query.strip()

        parts = query.split()

        building = None
        course = None
        teacher = None
        note_name = None

        # =========================
        # BUILDING
        # =========================

        if len(parts) >= 1:
            building = parts[0]

        # =========================
        # COURSE
        # =========================

        if len(parts) >= 2:

            try:
                course = int(parts[1])

            except:
                course = None

        # =========================
        # TEACHER
        # =========================

        if len(parts) >= 3:
            teacher = parts[2]

        # =========================
        # NOTE NAME
        # =========================

        if len(parts) >= 4:
            note_name = " ".join(parts[3:])

        # =========================
        # FILTERS
        # =========================

        filters = {"is_deleted": False}

        if building:
            filters["building_name__icontains"] = building

        if course:
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

            # =========================
            # DOCUMENT
            # =========================

            if note.telegram_file_type == "document":

                results.append(
                    InlineQueryResultCachedDocument(
                        id=f"doc_{note.id}",
                        title=note.note_name,
                        document_file_id=(note.telegram_file_id),
                        description=(
                            f"{note.building_name} | "
                            f"{note.course} курс | "
                            f"{note.teacher}"
                        ),
                    )
                )

            # =========================
            # PHOTO
            # =========================

            elif note.telegram_file_type == "photo":

                results.append(
                    InlineQueryResultCachedPhoto(
                        id=f"photo_{note.id}", photo_file_id=(note.telegram_file_id)
                    )
                )

        await inline_query.answer(results=results, cache_time=1, is_personal=True)

    except Exception:
        traceback.print_exc()
