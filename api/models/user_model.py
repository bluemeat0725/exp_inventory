from typing import List
from sqlalchemy.orm import declarative_base, registry, declared_attr
from sqlalchemy import UniqueConstraint, Column, Integer, String, BigInteger, Numeric, DateTime, JSON, inspect, text
from datetime import datetime
from sqlalchemy.dialects.mysql import insert

Base = declarative_base()


class Users(Base):
    """用户表模型"""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)

    oid = Column(String(50), nullable=False, unique=True, index=True, comment="msal 唯一标识")
    preferred_username= Column(String(100),  comment="msal用户名")
    display_name = Column(String(100),  comment="msal显示名称")


    

