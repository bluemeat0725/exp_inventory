import json
from contextlib import asynccontextmanager
from typing import Annotated
import logging

from fastapi import Depends
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool, StaticPool

from config import settings

# 配置日志
logger = logging.getLogger(__name__)


class CustomJSONEncoder(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        kwargs['ensure_ascii'] = False
        super().__init__(*args, **kwargs)


def get_database_config():
    """根据配置返回数据库连接参数"""
    if settings.DB_TYPE == 'postgresql':
        return {
            'url': settings.DATABASE_URL.replace("postgresql", "postgresql+asyncpg"),
            'sync_url': settings.DATABASE_URL.replace("postgresql", "postgresql+psycopg"),
            'pool_config': {
                'pool_size': 20,
                'max_overflow': 30,
                'pool_timeout': 30,
                'pool_recycle': 3600,
                'pool_pre_ping': True,
                'poolclass': QueuePool,
            },
            'connect_args': {
                "server_settings": {
                    "application_name": "sso_demo_api",
                },
                "command_timeout": 60,
            }
        }
    elif settings.DB_TYPE == 'sqlite':
        return {
            'url': settings.DATABASE_URL.replace("sqlite", "sqlite+aiosqlite"),
            'sync_url': settings.DATABASE_URL,
            'pool_config': {
                'poolclass': StaticPool,
                'pool_pre_ping': True,
                'pool_recycle': -1,  # SQLite不需要连接回收
            },
            'connect_args': {
                "check_same_thread": False,  # SQLite特定配置
            }
        }
    else:
        raise ValueError(f"Unsupported database type: {settings.DB_TYPE}")


# 获取数据库配置
db_config = get_database_config()

# 异步数据库引擎
db_engine = create_async_engine(
    db_config['url'],
    echo=False,  # 生产环境关闭SQL日志
    future=True,
    json_serializer=CustomJSONEncoder().encode,
    connect_args=db_config['connect_args'],
    **db_config['pool_config']
)

# 同步数据库引擎
sync_db_engine = create_engine(
    db_config['sync_url'],
    echo=False,
    json_serializer=CustomJSONEncoder().encode,
    connect_args=db_config['connect_args'],
    **{k: v for k, v in db_config['pool_config'].items() if k != 'pool_size' and k != 'max_overflow'}
)

# 优化的Session配置
SessionLocal = async_sessionmaker(
    bind=db_engine,
    expire_on_commit=False,
    autoflush=False,
    class_=AsyncSession
)

# 同步Session配置
SyncSessionLocal = sessionmaker(
    bind=sync_db_engine,
    expire_on_commit=False,
    autoflush=False,
)


# 优化的异步数据库依赖
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Async database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


# 优化的同步数据库依赖
def sync_get_db():
    session = SyncSessionLocal()
    try:
        yield session
    except Exception as e:
        logger.error(f"Sync database session error: {e}")
        session.rollback()
        raise
    finally:
        session.close()


# 上下文管理器版本 - 用于手动管理
@asynccontextmanager
async def async_get_db():
    """异步数据库上下文管理器"""
    async with SessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Async context database error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


# 数据库初始化函数
async def init_database():
    """初始化数据库（创建表等）"""
    try:
        from models.base import Base  # 假设你有一个Base模型

        if settings.DB_TYPE == 'sqlite':
            # 对于SQLite，使用同步引擎创建表
            Base.metadata.create_all(bind=sync_db_engine)
            logger.info("SQLite database tables created successfully")
        elif settings.DB_TYPE == 'postgresql':
            # 对于PostgreSQL，可以使用异步方式
            async with db_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("PostgreSQL database tables created successfully")

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


# 类型注解
SessionDep = Annotated[AsyncSession, Depends(get_db)]
SyncSessionDep = Annotated[sessionmaker, Depends(sync_get_db)]
