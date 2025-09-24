from functools import wraps
from typing import Union

from fastapi import HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED

from azure_sso import UserInfo
from common.user_service import get_current_user, header_scheme
from connector.con_redis import sync_cacheDep, cacheDep, get_redis
import redis
from connector.sql import *
from models import Users


async def trados_sys(token: str = Depends(header_scheme)):
    if token == settings.TRADOS_TOKEN:
        return 'trados'
    raise HTTPException(status_code=401, detail="Invalid trados token")


async def current_user_obj(token: str = Depends(header_scheme),
                           redis_client: Union[None, redis.Redis] = Depends(get_redis),
                           db: AsyncSession = Depends(get_db)
                           ) -> Users:
    return await get_current_user(token, redis_client, db, get_info=False)


async def current_user(token: str = Depends(header_scheme),
                       redis_client: Union[None, redis.Redis] = Depends(get_redis),
                       db: AsyncSession = Depends(get_db)) -> UserInfo:
    user = await get_current_user(token, redis_client, db)
    return user


async def admin_user(token: str = Depends(header_scheme),
                     redis_client: Union[None, redis.Redis] = Depends(get_redis),
                     db: AsyncSession = Depends(get_db)) -> UserInfo:
    user = await get_current_user(token, redis_client, db)
    if user.is_active == False or user.role != 'admin':
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Not enough permissions")
    return user


userObjDep = Annotated[current_user_obj, Depends(current_user_obj)]
userDep = Annotated[current_user, Depends(current_user)]
adminDep = Annotated[admin_user, Depends(admin_user)]
