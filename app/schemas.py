import uuid

from datetime import datetime
from pydantic import BaseModel, EmailStr, constr

from app.config import settings


class UserBaseSchema(BaseModel):
    name: str
    email: EmailStr


class CreateUserSchema(UserBaseSchema):
    password: constr(regex=settings.PASSWORD_REGEX)
    role: str = 'user'
    verified: bool = True


class UpdateUserSchema(UserBaseSchema):
    role: str
    verified: bool


class LoginUserSchema(BaseModel):
    email: EmailStr
    password: constr(min_length=8)


class UserResponse(UserBaseSchema):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class StatusResponse(BaseModel):
    status: str


class TokensResponse(StatusResponse):
    access_token: str
    refresh_token: str
