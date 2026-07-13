from fastapi import APIRouter, HTTPException

from database.services import (
    get_users_service,
    get_or_create_user_service,
    is_admin_service,
    change_admin_service,
    change_uploaded_notes_service,
)
from api.schemas.user import (
    UserResponse,
    AdminStatusResponse,
    ChangeAdminBody,
    ChangeUploadedBody,
)

router = APIRouter()


@router.get("/", response_model=list[UserResponse], summary="Все пользователи")
async def list_users():

    return await get_users_service()


@router.post(
    "/{user_id}",
    response_model=UserResponse,
    status_code=201,
    summary="Получить или создать пользователя",
)
async def get_or_create_user(user_id: int):
    return await get_or_create_user_service(user_id=user_id)


@router.get(
    "/{user_id}/admin",
    response_model=AdminStatusResponse,
    summary="Статус администратора",
)
async def get_admin_status(user_id: int):
    result = await is_admin_service(user_id=user_id)
    if result.get("message"):
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@router.patch("/{user_id}/admin", summary="Изменить статус администратора")
async def set_admin_status(user_id: int, body: ChangeAdminBody):
    result = await change_admin_service(user_id=user_id, status=body.status)
    if result.get("message"):
        raise HTTPException(status_code=404, detail=result["message"])
    return {"detail": f"Статус администратора изменён на {body.status}"}


@router.patch(
    "/{user_id}/notes-count", summary="Изменить счётчик загруженных конспектов"
)
async def update_notes_count(user_id: int, body: ChangeUploadedBody):
    result = await change_uploaded_notes_service(user_id=user_id, amount=body.amount)
    if result.get("message"):
        raise HTTPException(status_code=404, detail=result["message"])
    return {"detail": f"Счётчик конспектов обновлён на {body.amount:+d}"}
