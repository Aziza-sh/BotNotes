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
    """Сигнал: автоматически увеличивает версию объекта при каждом сохранении."""
    instance.version += 1


class BaseORM(Model):
    """Абстрактная базовая модель — общие поля для всех таблиц."""

    id: int = fields.IntField(pk=True)

    created_at: datetime = fields.DatetimeField(auto_now_add=True)
    updated_at: datetime = fields.DatetimeField(auto_now=True)

    # Мягкое удаление: вместо DELETE просто выставляем флаг
    is_deleted: bool = fields.BooleanField(default=False)

    # Версия записи (растёт при каждом save)
    version: int = fields.IntField(default=0)

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        pre_save(cls)(_bump_version)

    class Meta:
        abstract = True


class User(BaseORM):
    """Пользователь бота."""

    # Telegram user_id (уникальный)
    user_id: int = fields.BigIntField(unique=True)

    # Сколько конспектов пользователь загрузил
    uploaded_notes: int = fields.IntField(default=0)

    # Флаг администратора
    is_admin: bool = fields.BooleanField(default=False)

    class Meta:
        table = "users"


class Notes(BaseORM):
    """Конспект, загруженный пользователем."""

    # Владелец конспекта
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User",
        related_name="notes",
        on_delete=fields.CASCADE,
    )

    # Telegram file_id (для пересылки файла без повторной загрузки)
    telegram_file_id: str = fields.TextField(null=True)
    telegram_file_type: str = fields.CharField(max_length=20, null=True)

    # Корпус / здание
    building_name: str = fields.CharField(max_length=200)

    # Курс (1–6)
    course: int = fields.IntField()

    # Преподаватель
    teacher: str = fields.CharField(max_length=300)

    # Название конспекта
    note_name: str = fields.CharField(max_length=300)

    # Путь к файлу на диске
    note_path: str = fields.CharField(max_length=500)
    

    class Meta:
        table = "notes"
