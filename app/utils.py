from typing import Callable
from functools import wraps
from fastapi import status, HTTPException
from passlib.context import CryptContext
from async_fastapi_jwt_auth import AuthJWT
from datetime import timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class ProcessPassword:
    @staticmethod
    def hash_password(password: str):
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(password: str, hashed_password: str):
        return pwd_context.verify(password, hashed_password)


class ProcessToken:
    @staticmethod
    async def generate_tokens(authorize: AuthJWT,
                              subject: str,
                              access_expires_time: int,
                              refresh_expires_time: int):
        access_token = await authorize.create_access_token(subject=subject,
                                                           expires_time=timedelta(minutes=access_expires_time))
        refresh_token = await authorize.create_refresh_token(subject=subject,
                                                             expires_time=timedelta(days=refresh_expires_time))
        return access_token, refresh_token


def error_handling(token_type: str):
    def check_error(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error = e.__class__.__name__
                if error == 'MissingTokenError':
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST, detail=f'Please provide {token_type} token'
                    )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=error
                )
        return wrapper
    return check_error
