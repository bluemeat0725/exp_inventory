from typing import AsyncIterator, Annotated

import redis
from fastapi import Depends

from config import settings

'''
https://redis-py.readthedocs.io/en/stable/examples/asyncio_examples.html#Connecting-and-Disconnecting
'''

redis_pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True, max_connections=100)
aredis_pool = redis.asyncio.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True, socket_timeout=10)


def sync_get_redis() -> redis.Redis:
    return redis.Redis(connection_pool=redis_pool)


async def get_redis() -> AsyncIterator[redis.asyncio.Redis]:
    client = redis.asyncio.Redis(connection_pool=aredis_pool)
    yield client
    await client.aclose()


sync_cacheDep = Annotated[redis.Redis, Depends(sync_get_redis)]
cacheDep = Annotated[AsyncIterator[redis.asyncio.Redis], Depends(get_redis)]
