from pydantic import BaseModel, ConfigDict


class NoteCreate(BaseModel):

    user_id: int
    building_name: str
    course: int
    teacher: str
    note_name: str
    note_path: str
    telegram_file_id: str
    telegram_file_type: str


class NoteResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    building_name: str
    course: int
    teacher: str
    note_name: str
    note_path: str
    telegram_file_id: str | None
    telegram_file_type: str | None
    is_deleted: bool


class NoteUpdate(BaseModel):

    building_name: str | None = None
    course: int | None = None
    teacher: str | None = None
    note_name: str | None = None
    is_deleted: bool | None = None
