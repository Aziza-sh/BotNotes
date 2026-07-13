from pydantic import BaseModel


class AISummaryResponse(BaseModel):
    note_id: int
    summary: str
