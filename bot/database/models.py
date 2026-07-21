from datetime import datetime
from typing import Any

from tortoise import fields
from tortoise.models import Model
from tortoise.signals import pre_save


async def _bump_version(
    sender: Any,
    instance: "BaseORM",
    using_db: Any,
    update_fields: Any,
) -> None:

    instance.version += 1


class BaseORM(Model):

    id: int = fields.IntField(pk=True)

    created_at: datetime = fields.DatetimeField(auto_now_add=True)
    updated_at: datetime = fields.DatetimeField(auto_now=True)

    is_deleted: bool = fields.BooleanField(default=False)

    version: int = fields.IntField(default=0)

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        pre_save(cls)(_bump_version)

    class Meta:
        abstract = True


class User(BaseORM):

    user_id: int = fields.BigIntField(unique=True)

    uploaded_notes: int = fields.IntField(default=0)

    messages_sent: int = fields.IntField(default=0)

    is_admin: bool = fields.BooleanField(default=False)

    class Meta:
        table = "users"


class CustomTeacher(BaseORM):

    course: int = fields.IntField()

    full_name: str = fields.CharField(max_length=300)

    class Meta:
        table = "custom_teachers"


class Notes(BaseORM):
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User",
        related_name="notes",
        on_delete=fields.CASCADE,
    )

    telegram_file_id: str = fields.TextField(null=True)
    telegram_file_type: str = fields.CharField(max_length=20, null=True)

    building_name: str = fields.CharField(max_length=200)

    course: int = fields.IntField()

    teacher: str = fields.CharField(max_length=300)

    note_name: str = fields.CharField(max_length=300)

    note_path: str = fields.CharField(max_length=500)

    class Meta:
        table = "notes"
