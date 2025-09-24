from typing import Optional, Union

import redis
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.sql.expression import select
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from azure_sso import UserInfo
from config import settings

from connector.con_redis import get_redis
from connector.sql import get_db
from common.security import verify_token
from models import Users


class CustomAuthHeader(APIKeyHeader):

    async def __call__(self, request: Request) -> Optional[str]:
        api_key = request.headers.get(self.model.name)
        if not api_key:
            api_key = request.cookies.get("access_token")
        if not api_key:
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
                )
            else:
                return None
        if api_key.startswith(settings.AUTH_HEADER_TYPE):
            api_key = api_key.split(" ", maxsplit=2)[-1]
        return api_key


header_scheme = CustomAuthHeader(name=settings.AUTH_HEADER_NAME)


def get_user_payload(token: str = Depends(header_scheme)) -> dict:
    try:
        payload = verify_token(token)
    except Exception as e:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=f"Signature verification failed.",
                            headers={"WWW-Authenticate": "Bearer"})
    return payload


async def user_logout(token: str, exp, aredis_client: redis.asyncio.Redis):
    await aredis_client.set(f'logout:user:{token}', token)
    await aredis_client.expireat(f'logout:user:{token}', exp)


async def check_logout(token: str, aredis_client: redis.asyncio.Redis):
    key = f'logout:user:{token}'
    token_user_id = await aredis_client.exists(key)
    if token_user_id:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Token has been revoked.")


async def get_current_user(token: str = Depends(header_scheme),
                           redis_client: Union[None, redis.asyncio.Redis] = Depends(get_redis),
                           db: AsyncSession = Depends(get_db)) -> UserInfo:
    payload = get_user_payload(token)
    oid = payload.get('oid')
    if oid is None:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid token.")
    await check_logout(token=token, aredis_client=redis_client)
    user = (await db.execute(select(Users).where(Users.oid == oid))).scalars().first()
    user_info = UserInfo.model_validate(user)
    return user_info
