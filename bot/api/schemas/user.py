from pydantic import BaseModel


class UserResponse(BaseModel):
    user_id: int


class AdminStatusResponse(BaseModel):
    status: bool


class ChangeAdminBody(BaseModel):
    status: bool


class ChangeUploadedBody(BaseModel):
    amount: int


class UserStatisticResponse(BaseModel):
    uploaded_notes: int
