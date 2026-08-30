from pydantic import BaseModel


class TeachersResponse(BaseModel):
    teachers: list[str]
