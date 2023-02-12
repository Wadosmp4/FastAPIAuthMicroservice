from abc import ABC
from typing import Dict

from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import CreateUserSchema
from app.models import User, Base
from app.utils import ProcessPassword


class BaseController(ABC):
    model = None

    @classmethod
    async def create(cls, db: AsyncSession, data: Dict):
        new_instance = cls.model(**data)
        db.add(new_instance)
        await db.commit()
        await db.refresh(new_instance)
        return new_instance

    @classmethod
    async def get(cls, db: AsyncSession, obj_id: str):
        return (await db.execute(
            select(cls.model).filter(cls.model.id == obj_id)
        )).scalar()

    @classmethod
    async def all(cls, db: AsyncSession):
        return [el[0] for el in (await db.execute(select(cls.model)))]

    @classmethod
    async def update(cls, db: AsyncSession, obj: Base, data: Dict):
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    @classmethod
    async def delete(cls, db: AsyncSession, obj):
        await db.delete(obj)
        await db.commit()
        return True


class UserController(BaseController):
    model = User

    @classmethod
    async def get_by_email(cls, db: AsyncSession, email: EmailStr):
        return (await db.execute(
            select(cls.model).filter(cls.model.email == email)
        )).scalar()

    @staticmethod
    def transform_payload(payload: CreateUserSchema):
        payload.password = ProcessPassword.hash_password(payload.password)
        payload.verified = True
        payload.email = EmailStr(payload.email.lower())
        return payload
