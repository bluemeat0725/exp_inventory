import os.path
from datetime import timedelta
from typing import Optional, Union, Literal
from urllib.parse import quote_plus

from pydantic import Field, BaseModel, model_validator, field_validator
from pydantic_settings import SettingsConfigDict
from pydantic_settings import BaseSettings


def parse_timedelta(days, minutes, seconds):
    class DeltaVars(BaseModel):
        days: int
        minutes: int
        seconds: int

    var = DeltaVars(days=days, minutes=minutes, seconds=seconds)
    return timedelta(**var.model_dump())


class ProjectConfig(BaseModel):
    """
    Project configs
    """
    APP_TITLE: Optional[str] = Field(description='application name', default='sso-demo')
    DEBUG: Optional[bool] = Field(description='debug mode', default=False)
    DESCRIPTION: Optional[str] = Field(description='application description', default='')
    VERSION: Optional[str] = '0.2.0'
    MODE: Optional[str] = None
    FRONTEND_URL: Optional[str] = ''


class DatabaseConfig(BaseModel):
    """
    数据库类型选择配置
    """
    DB_TYPE: Literal['postgresql', 'sqlite'] = Field(description='数据库类型', default='sqlite')
    DATABASE_URL: str = ''  # 最终生成的数据库URL


class PgSqlConfig(BaseModel):
    PGSQL_HOST: Optional[str] = 'localhost'
    PGSQL_PORT: Optional[int] = 5432
    PGSQL_NAME: Optional[str] = 'sso_demo'
    PGSQL_USER: Optional[str] = 'postgres'
    PGSQL_PASSWORD: Optional[str] = 'password'
    PGSQL_URL: str = ''


class SqliteConfig(BaseModel):
    """
    SQLite数据库配置
    """
    SQLITE_PATH: Optional[str] = Field(description='SQLite数据库文件路径', default='./data/sso_demo.db')
    SQLITE_URL: str = ''

    @field_validator('SQLITE_PATH', mode='after')
    @classmethod
    def ensure_directory(cls, v):
        """确保SQLite数据库文件的目录存在"""
        if v:
            directory = os.path.dirname(v)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
        return v


class RedisConfig(BaseModel):
    REDIS_HOST: Optional[str] = '127.0.0.1'
    REDIS_PORT: Optional[int] = 6379
    REDIS_DB: Optional[int] = 0
    REDIS_ENCODING: Optional[str] = 'utf-8'
    REDIS_USERNAME: Optional[str] = None
    REDIS_PASS: Optional[str] = None
    REDIS_URL: Optional[str] = None
    REDIS_SSL: Optional[bool] = False


class JWTConfig(BaseModel):
    ACCESS_TOKEN_LIFETIME: Union[list, str, timedelta] = '00-00-20'  # days minutes seconds
    ALGORITHM: str = "HS256"
    AUTH_HEADER_TYPE: Optional[str] = "Bearer"
    AUTH_HEADER_NAME: str = "Authorization"
    SECRET_KEY: Optional[str] = 'renyuan.a.wang.super.secret.key.for.session.middleware.should.be.at.least.32.chars'

    @field_validator('ACCESS_TOKEN_LIFETIME')
    def validate_timedelta(cls, v):
        if isinstance(v, timedelta):
            return v
        elif isinstance(v, list):
            return parse_timedelta(*v)
        elif isinstance(v, str):
            var = v.split('-')
            return parse_timedelta(*var)
        else:
            raise ValueError('token_lifetime or refresh_token_lifetime config error')


class AzureSSO(BaseModel):
    AAD_CLIENT_ID: Optional[str]
    AAD_TENANT_ID: Optional[str]
    AAD_SECRETKEY: Optional[str] = None
    AAD_CERTIFICATE_THUMBPRINT: Optional[str] = None
    AAD_PRIVATE_KEY_FILE: Optional[str] = 'private_key.pem'
    AAD_REDIRECT_END_POINT: Optional[str] = '/login/callback'

    @field_validator('AAD_PRIVATE_KEY_FILE', mode='after')
    @classmethod
    def get_key(cls, v):
        if not v:
            return v
        else:
            path = os.path.join('.', 'cert', v)
            return path


class LoadConfig(BaseSettings,
                 ProjectConfig,
                 DatabaseConfig,
                 JWTConfig,
                 PgSqlConfig,
                 SqliteConfig,
                 RedisConfig,
                 AzureSSO
                 ):
    model_config = SettingsConfigDict(
        # read from dotenv format config file
        env_file='.env',
        env_file_encoding='utf-8',
        env_ignore_empty=True,
        # ignore extra attributes
        extra='ignore',
    )

    @model_validator(mode='after')
    @classmethod
    def url(cls, values):
        # PostgreSQL URL生成
        if issubclass(cls, PgSqlConfig) and values.PGSQL_HOST:
            url = f'{values.PGSQL_USER}:{quote_plus(values.PGSQL_PASSWORD)}@{values.PGSQL_HOST}:{values.PGSQL_PORT}/{values.PGSQL_NAME}'
            values.PGSQL_URL = f'postgresql://{url}'
        
        # SQLite URL生成
        if issubclass(cls, SqliteConfig):
            # 转换为绝对路径
            sqlite_path = os.path.abspath(values.SQLITE_PATH)
            values.SQLITE_URL = f'sqlite:///{sqlite_path}'
        
        # 根据DB_TYPE设置最终的DATABASE_URL
        if issubclass(cls, DatabaseConfig):
            if values.DB_TYPE == 'postgresql':
                values.DATABASE_URL = values.PGSQL_URL
            elif values.DB_TYPE == 'sqlite':
                values.DATABASE_URL = values.SQLITE_URL
        
        # Redis URL生成
        if issubclass(cls, RedisConfig):
            if values.REDIS_SSL:
                redis = 'rediss'
            else:
                redis = 'redis'
            if values.REDIS_USERNAME and values.REDIS_PASS:
                values.REDIS_URL = f'{redis}://{values.REDIS_USERNAME}:{quote_plus(values.REDIS_PASS)}@{values.REDIS_HOST}:{values.REDIS_PORT}/{values.REDIS_DB}/?encoding={values.REDIS_ENCODING}'
            elif values.REDIS_PASS:
                values.REDIS_URL = f'{redis}://:{quote_plus(values.REDIS_PASS)}@{values.REDIS_HOST}:{values.REDIS_PORT}/{values.REDIS_DB}/?encoding={values.REDIS_ENCODING}'
            else:
                values.REDIS_URL = f'{redis}://{values.REDIS_HOST}:{values.REDIS_PORT}/{values.REDIS_DB}/?encoding={values.REDIS_ENCODING}'
        
        return values


settings = LoadConfig()
if settings.MODE == 'dev':
    print('proj config:\n', settings.model_dump_json(indent=4))
