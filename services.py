'''
Module for service methods
'''

from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext
from fastapi import HTTPException

from users import users_db, UserInDB


'''Hash password context'''
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    '''Hash password.'''
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    '''Verify that hashed password is valid and exists.'''
    return pwd_context.verify(plain_password, hashed_password)


def register_user(username: str, password: str) -> None:
    '''Register user in db.'''
    try:
        if username in users_db:
            raise HTTPException(status_code=400, detail="Username already registered")
        users_db[username] = get_password_hash(password)
    except Exception as e:
        print(f"Error during registration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during registration")


def get_user(users_db, username: str):
    '''Get user from db.'''
    if username in users_db:
        user_data = {'username': username, 'hashed_password': users_db[username]}
        return UserInDB(**user_data)
    return None


def authenticate_user(users_db, username: str, password: str):
    '''Check if the user exists and credentials are valid.'''
    user = get_user(users_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_token(data: dict, expires_delta: timedelta | None = None):
    '''Create and encode token with expiration time.'''
    from config import SECRET_KEY, ALGORITHM
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt