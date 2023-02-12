from datetime import timedelta
from pydantic import EmailStr

from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils import ProcessPassword, ProcessToken, error_handling
from app.database import get_db
from app.oauth2 import AuthJWT, redis_conn
from app.config import settings
from app.controllers import UserController
from app.schemas import CreateUserSchema, UserResponse, LoginUserSchema, TokensResponse, StatusResponse


router = APIRouter()
ACCESS_TOKEN_EXPIRES_IN = settings.ACCESS_TOKEN_EXPIRES_IN
REFRESH_TOKEN_EXPIRES_IN = settings.REFRESH_TOKEN_EXPIRES_IN


@router.post('/register',
             status_code=status.HTTP_201_CREATED,
             response_model=UserResponse)
async def create_user(payload: CreateUserSchema, db: AsyncSession = Depends(get_db)):
    user = await UserController.get_by_email(db, EmailStr(payload.email.lower()))
    if user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail='Account already exist')

    payload = UserController.transform_payload(payload)
    new_user = await UserController.create(db, payload)
    return new_user


@router.post('/login',
             status_code=status.HTTP_200_OK,
             response_model=TokensResponse)
async def login(payload: LoginUserSchema, db: AsyncSession = Depends(get_db), Authorize: AuthJWT = Depends()):
    user = await UserController.get_by_email(db, EmailStr(payload.email.lower()))
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Incorrect Email or Password')

    if not user.verified:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Please verify your email address')

    if not ProcessPassword.verify_password(payload.password, user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Incorrect Email or Password')

    access_token, refresh_token = await ProcessToken.generate_tokens(authorize=Authorize,
                                                                     subject=str(user.id),
                                                                     access_expires_time=ACCESS_TOKEN_EXPIRES_IN,
                                                                     refresh_expires_time=REFRESH_TOKEN_EXPIRES_IN)

    return {'status': 'success', 'access_token': access_token, 'refresh_token': refresh_token}


@error_handling('refresh')
@router.post('/token/refresh',
             status_code=status.HTTP_200_OK,
             response_model=TokensResponse)
async def refresh_access_token(Authorize: AuthJWT = Depends(), db: AsyncSession = Depends(get_db)):
    await Authorize.jwt_refresh_token_required()

    jti = (await Authorize.get_raw_jwt())['jti']
    user_id = await Authorize.get_jwt_subject()
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not refresh access token')
    user = await UserController.get(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='The user belonging to this token no longer exist')

    await redis_conn.setex(jti, timedelta(days=REFRESH_TOKEN_EXPIRES_IN), 'expired')

    access_token, refresh_token = await ProcessToken.generate_tokens(authorize=Authorize,
                                                                     subject=str(user.id),
                                                                     access_expires_time=ACCESS_TOKEN_EXPIRES_IN,
                                                                     refresh_expires_time=REFRESH_TOKEN_EXPIRES_IN)

    return {'status': 'success', 'access_token': access_token, 'refresh_token': refresh_token}


@error_handling('access')
@router.get('/token/verify',
            status_code=status.HTTP_200_OK,
            response_model=UserResponse)
async def get_me(db: AsyncSession = Depends(get_db), Authorize: AuthJWT = Depends()):
    await Authorize.jwt_required()
    user_id = await Authorize.get_jwt_subject()
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not refresh access token')
    user = await UserController.get(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='The user belonging to this token no longer exist'
        )
    return user


@error_handling('access')
@router.delete('/revoke/access',
               status_code=status.HTTP_200_OK,
               response_model=StatusResponse)
async def access_revoke(Authorize: AuthJWT = Depends()):
    await Authorize.jwt_required()

    jti = (await Authorize.get_raw_jwt())['jti']
    await redis_conn.setex(jti, timedelta(minutes=ACCESS_TOKEN_EXPIRES_IN), 'expired')
    return {"status": "success"}


@error_handling('refresh')
@router.delete('/revoke/refresh',
               status_code=status.HTTP_200_OK,
               response_model=StatusResponse)
async def refresh_revoke(Authorize: AuthJWT = Depends()):
    await Authorize.jwt_refresh_token_required()

    jti = (await Authorize.get_raw_jwt())['jti']
    await redis_conn.setex(jti, timedelta(days=REFRESH_TOKEN_EXPIRES_IN), 'expired')
    return {"status": "success"}
