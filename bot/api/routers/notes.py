import mimetypes
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from database.services import (
    get_notes_service,
    create_note_service,
    delete_note_service,
    get_teachers,
    get_teacher_note_service,
    search_notes_inline,
    get_note_by_id_service,
)
from functions.storage import download_to_temp, object_exists
from api.schemas.note import NoteCreate, NoteResponse, NoteUpdate
from api.schemas.search import SearchNoteResponse
from api.schemas.teacher import TeachersResponse

router = APIRouter()


@router.get("/", response_model=list[NoteResponse], summary="Все конспекты")
async def list_notes():
    return await get_notes_service()


@router.post(
    "/", response_model=NoteResponse, status_code=201, summary="Создать конспект"
)
async def create_note(body: NoteCreate):
    result = await create_note_service(
        user_id=body.user_id,
        building_name=body.building_name,
        course=body.course,
        teacher=body.teacher,
        note_name=body.note_name,
        note_path=body.note_path,
        telegram_file_id=body.telegram_file_id,
        telegram_file_type=body.telegram_file_type,
    )
    if result.get("message"):
        raise HTTPException(status_code=404, detail=result["message"])

    note = result["data"]
    return {
        "id": note.id,
        "user_id": body.user_id,
        "building_name": note.building_name,
        "course": note.course,
        "teacher": note.teacher,
        "note_name": note.note_name,
        "note_path": note.note_path,
        "telegram_file_id": note.telegram_file_id,
        "telegram_file_type": note.telegram_file_type,
        "is_deleted": note.is_deleted,
    }


@router.delete("/{note_id}", summary="Удалить конспект")
async def delete_note(note_id: int):
    result = await delete_note_service(note_id)
    if result.get("message"):
        raise HTTPException(status_code=404, detail=result["message"])
    return {"detail": "Конспект удалён"}


@router.get("/{note_id}/file", summary="Скачать файл конспекта")
async def download_note_file(note_id: int):
    note = await get_note_by_id_service(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Конспект не найден")

    if not note.note_path:
        raise HTTPException(status_code=404, detail="Файл конспекта отсутствует")

    if not await object_exists(note.note_path):
        raise HTTPException(
            status_code=404, detail="Файл конспекта не найден в хранилище"
        )

    tmp_path = await download_to_temp(note.note_path)

    ext = Path(note.note_path).suffix
    filename = f"{note.note_name}{ext}" if ext else note.note_name
    media_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    return FileResponse(
        path=tmp_path,
        media_type=media_type,
        filename=filename,
        background=BackgroundTask(os.remove, tmp_path),
    )


@router.get(
    "/search", response_model=list[SearchNoteResponse], summary="Поиск конспектов"
)
async def search_notes(
    q: str = Query(..., description="корпус_курс_преподаватель_конспект"),
):
    notes = await search_notes_inline(q)
    return [
        {
            "id": n.id,
            "building_name": n.building_name,
            "course": n.course,
            "teacher": n.teacher,
            "note_name": n.note_name,
            "telegram_file_id": n.telegram_file_id,
        }
        for n in notes
    ]


@router.get(
    "/teachers", response_model=TeachersResponse, summary="Список преподавателей"
)
async def list_teachers(
    course: int = Query(...),
    building_name: str = Query(...),
):
    teachers = await get_teachers(course=course, building_name=building_name)
    return {"teachers": teachers}


@router.get(
    "/by-teacher", response_model=list[NoteResponse], summary="Конспекты преподавателя"
)
async def notes_by_teacher(
    name: str = Query(...),
    course: int = Query(...),
    building_name: str = Query(...),
):
    return await get_teacher_note_service(
        name=name, course=course, building_name=building_name
    )
