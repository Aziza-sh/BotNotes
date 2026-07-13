from fastapi import APIRouter, HTTPException

from database.models import Notes
from api.schemas.ai import AISummaryResponse

router = APIRouter()


@router.get(
    "/summary/{note_id}",
    response_model=AISummaryResponse,
    summary="Краткое резюме конспекта",
)
async def get_note_summary(note_id: int):
    """
    Возвращает краткое резюме конспекта по его ID.

    Сейчас резюме составляется из мета-данных (корпус, курс, преподаватель,
    название). В будущем сюда можно подключить LLM для анализа текста файла.
    """
    note = await Notes.get_or_none(id=note_id, is_deleted=False)
    if not note:
        raise HTTPException(status_code=404, detail="Конспект не найден")

    summary = (
        f"Конспект «{note.note_name}» "
        f"по дисциплине преподавателя {note.teacher}, "
        f"{note.course} курс, "
        f"учебное заведение: {note.building_name}."
    )

    return AISummaryResponse(note_id=note.id, summary=summary)
