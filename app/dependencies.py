from async_fastapi_jwt_auth import AuthJWT
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import UserController
from app.utils import error_handling
from app.database import get_db


@error_handling('access')
async def get_current_user(db: AsyncSession = Depends(get_db), Authorize: AuthJWT = Depends()):
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