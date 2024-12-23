from datetime import timedelta
from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import pybreaker

from users import users_db, Token
from services import authenticate_user, create_token, register_user, external_api_call
from config import ACCESS_TOKEN_EXPIRE_MINUTES


app = FastAPI()

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

circuit_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=10)


@app.get('/')
def root():
    '''
    Check if server is running
    '''
    return {'message': 'This is a root endpoint!!'}


@app.post('/register')
async def register(username: str, password: str):
    '''
    Register new user
    '''
    register_user(username, password)
    return {"message": "User registered successfully!!"}


@app.post('/token')
@limiter.limit("3/minute")
async def login(request: Request, form_data: Annotated[OAuth2PasswordRequestForm, Depends()],) -> Token:
    '''
    Log in and retrieve token endpoint.
    Rate limiting implemented.
    '''
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


@app.exception_handler(pybreaker.CircuitBreakerError)
async def circuit_breaker_error_handler(request, exc):
    raise HTTPException(status_code=503, detail="Service temporarily unavailable")


@app.get('/circuitbreak')
@circuit_breaker
def test_cb():
    '''
    Test endpoint for circuit breaker functionality
    '''
    result = external_api_call()
    return result
