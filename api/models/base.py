from typing import List
from sqlalchemy.orm import declarative_base, registry, declared_attr
from sqlalchemy import UniqueConstraint, Column, Integer, String, BigInteger, Numeric, DateTime, JSON, inspect, text
from datetime import datetime
from sqlalchemy.dialects.mysql import insert

Base = declarative_base()


class ModelBase(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)

    created_at = Column(DateTime, nullable=True, comment="创建时间", default=datetime.now, index=True)
    updated_at = Column(DateTime, nullable=True, comment="更新时间", default=datetime.now, index=True)


def init_vector():
    from connector.sql import sync_get_db
    db = next(sync_get_db())
    try:
        vector_init_sql = 'CREATE EXTENSION vector;'
        db.execute(text(vector_init_sql))
        db.commit()
        print('向量数据库初始化成功')
    except Exception as e:
        pass


