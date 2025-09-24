from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt
from fastapi import Header
import bcrypt

from config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # bcrypt expects the hashed password to be in bytes
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)


def get_password_hash(password: str) -> str:
    # Generate a salt and create a hash
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    # Convert the hashed password to a string for storage
    return hashed_password.decode('utf-8')


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + settings.ACCESS_TOKEN_LIFETIME
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str, validate_token_type=False, check_expire=False):
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


class LoadAuthorizationHeader:
    def __call__(self, authorization: str = Header(None)) -> Optional[str]:
        return authorization
