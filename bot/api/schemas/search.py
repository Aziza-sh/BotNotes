from pydantic import BaseModel


class SearchNoteResponse(BaseModel):
    id: int

    building_name: str
    course: int
    teacher: str

    note_name: str

    telegram_file_id: str | None
