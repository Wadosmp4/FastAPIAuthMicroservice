from typing import List
from pydantic import EmailStr

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status, APIRouter, Depends, HTTPException

from app.database import get_db
from app.roles import RoleChecker
from app.schemas import UserResponse, CreateUserSchema, UpdateUserSchema, StatusResponse
from app.controllers import UserController

router = APIRouter()
allow_manage_users = RoleChecker(['admin'])


@router.post('/',
             status_code=status.HTTP_201_CREATED,
             response_model=UserResponse,
             dependencies=[Depends(allow_manage_users)])
async def create_user(payload: CreateUserSchema, db: AsyncSession = Depends(get_db)):
    user = await UserController.get_by_email(db, EmailStr(payload.email.lower()))
    if user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail='Account already exist')

    payload = UserController.transform_payload(payload)
    new_user = await UserController.create(db, payload.dict())
    return new_user


@router.delete('/{user_id}',
               status_code=status.HTTP_200_OK,
               response_model=StatusResponse,
               dependencies=[Depends(allow_manage_users)])
async def delete_user(user_id: str, db: AsyncSession = Depends(get_db)):
    user = await UserController.get(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='User does not exist')

    await UserController.delete(db, user)
    return {'status': 'success'}


@router.get('/{user_id}',
            status_code=status.HTTP_200_OK,
            response_model=UserResponse,
            dependencies=[Depends(allow_manage_users)])
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    user = await UserController.get(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'No users with {user_id} id')
    return user


@router.get('/',
            status_code=status.HTTP_200_OK,
            response_model=List[UserResponse],
            dependencies=[Depends(allow_manage_users)])
async def get_all_users(db: AsyncSession = Depends(get_db)):
    users = await UserController.all(db)
    if not users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'No users found')
    return users


@router.put('/{user_id}',
            status_code=status.HTTP_200_OK,
            response_model=UserResponse,
            dependencies=[Depends(allow_manage_users)])
async def update_user(user_id: str, payload: UpdateUserSchema, db: AsyncSession = Depends(get_db)):
    user = await UserController.get(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='User does not exist')
    updated_user = await UserController.update(db, user, payload.dict())
    return updated_user
