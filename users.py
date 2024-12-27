'''
Module for data models
'''

from pydantic import BaseModel


class Token(BaseModel):
    '''Structure of token response'''
    access_token: str
    token_type: str


class TokenData(BaseModel):
    '''Data of token'''
    username: str | None = None


class UserRegistration(BaseModel):
    username: str 
    password: str

class User(BaseModel):
    username: str


class UserInDB(User):
    '''Extends the User model with hashed password data.'''
    hashed_password: str


'''
Mock database for storing users data.
'''
users_db: dict[str, str] = {}