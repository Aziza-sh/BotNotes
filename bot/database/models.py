from datetime import datetime
from typing import Any

from tortoise import fields
from tortoise.models import Model
from tortoise.signals import pre_save


async def pre_save_model(
    sender: Any,
    instance: "BaseORM",
    using_db,
    update_fields,
) -> None:
    instance.version += 1


class BaseORM(Model):
    id: int = fields.IntField(pk=True)

    created_at: datetime = fields.DatetimeField(auto_now_add=True)
    updated_at: datetime = fields.DatetimeField(auto_now=True)

    # Мягкое удаление
    is_deleted: bool = fields.BooleanField(default=False)

    # Версия объекта
    version: int = fields.IntField(default=0)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        pre_save(cls)(pre_save_model)

    class Meta:
        abstract = True


class User(BaseORM):
    # Telegram user id
    user_id: int = fields.BigIntField(unique=True)

    uploaded_notes: int = fields.IntField(default=0)

    is_admin: bool = fields.BooleanField(default=False)

    class Meta:
        table = "users"


class Notes(BaseORM):
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User",
        related_name="notes",
        on_delete=fields.CASCADE,
    )

    building_name: str = fields.CharField(max_length=200)
    course: int = fields.IntField(default=0)

    teacher: str = fields.CharField(max_length=300)

    note_name: str = fields.CharField(max_length=200)

    note_path: str = fields.CharField(max_length=300)

    class Meta:
        table = "notes"