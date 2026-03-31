from datetime import datetime
from typing import Any

from tortoise import fields
from tortoise.models import Model
from tortoise.signals import pre_save


async def pre_save_model(
    sender: Any,
    instance: "BaseORM",
    using_db: str,
    update_fields: list[str],
) -> None:
    instance.version += 1


class BaseORM(Model):
    id: int = fields.IntField(pk=True)
    created_at: datetime = fields.DatetimeField(auto_now_add=True)
    updated_at: datetime = fields.DatetimeField(auto_now=True)
    is_deleted: bool = fields.BooleanField(default=False) # Для возможности не удалять объекты из бд, но помечать их как удаленные
    version: int = fields.IntField(default=0) # Для возможности отследить кол-во изменений объекта

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        pre_save(cls)(pre_save_model)

    class Meta:
        abstract = True


class User(BaseORM): # Для пользователей
    user_id = fields.BigIntField()
    uploaded_notes: int = fields.IntField(default=0)
    is_admin: int = fields.BooleanField(default=False)


class Notes(BaseORM):
    user = fields.ForeignKeyField(
        model_name='models.User', 
        related_name='notes'
    )
    course: int = fields.IntField(default=0)
    teacher: str = fields.CharField(max_length=300)
    note_name: str = fields.CharField(max_length=200)
    note_path: str = fields.CharField(max_length=300)
