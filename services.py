'''
Module for service methods
'''
import random
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext
from fastapi.responses import JSONResponse
from fastapi import HTTPException

from users import users_db, UserInDB, TokenData
from config import ALGORITHM, SECRET_KEY


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
    if username in users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    users_db[username] = get_password_hash(password)
    return


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


async def verify_token(token: str) -> TokenData:
    '''
    Verify the given JWT token.
    Args:
        token: JWT token string.
    Returns:
        TokenData: decoded token data if valid, otherwise raises exception
    '''
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        expire = payload.get('exp')

        if expire is not None:
            expire_time = datetime.fromtimestamp(expire, tz=timezone.utc)
            if expire_time < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=401, 
                    detail='Token expired',
                    headers={'WWW-Authenticate': 'Bearer'}
                )
        
        if username is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token_data = TokenData(username=username)
        return token_data

    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Error decoding token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def external_api_call():
    '''Simulate usage of external API for Circuit Breaker testing endpoint'''
    if random.choice([True, False]):
        return {'message': 'Failure simulated'}
    return {'message': 'Success simulated'}
