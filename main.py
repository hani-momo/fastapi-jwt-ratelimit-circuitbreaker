from datetime import timedelta
from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
import jwt


from users import users_db, Token
from services import authenticate_user, create_token, register_user
from config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM


app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
key = 'secret'
encoded = jwt.encode({'some': 'payload'}, key, ALGORITHM)
jwt.decode(encoded, key, algorithms=['HS256'])


@app.get('/')
def root():
    return {'message': 'This is a root endpoint!!'}


@app.post('/register')
def register(username: str, password: str):
    '''
    Register new user
    '''
    register_user(username, password)
    return {"message": "User registered successfully!!"}


@app.post('/token')
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],) -> Token:
    '''Log in and retrieve token endpoint.'''

    user = authenticate_user(users_db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_token(data={'sub': user.username}, expires_delta=access_token_expires)

    return {'access_token': access_token, 'token_type': 'bearer', 'message':'successfully logged in!!'}
