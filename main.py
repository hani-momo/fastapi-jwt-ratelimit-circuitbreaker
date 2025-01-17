import logging
from datetime import timedelta
from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm

from config import oauth2_scheme

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import pybreaker

from data import users_db, Token, UserRegistration
from services import (
    authenticate_user, create_token,
    register_user,
    verify_token
    )
from config import ACCESS_TOKEN_EXPIRE_MINUTES


logger = logging.getLogger(__name__)

app = FastAPI()

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

circuit_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=5)


class ExternalAPIAdapter:
    def external_api_call(self):
        return 'hello'


@app.get('/')
def root():
    return {'message': 'This is a root endpoint!!'}


@app.post('/register', status_code=201)
async def register(user_data: UserRegistration):
    register_user(user_data.username, user_data.password)
    return {"message": "User registered successfully!!"}


@app.post('/login')
@limiter.limit("3/minute")
async def login(request: Request, form_data: Annotated[OAuth2PasswordRequestForm, Depends()],) -> Token:
    user = authenticate_user(users_db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=401,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_token(data={'sub': user.username}, expires_delta=access_token_expires)

    return {
        'access_token': access_token, 
        'token_type': 'bearer', 
        'message':'successfully logged in!!'
    }


@app.get('/protected')
async def protected_route(token: str = Depends(oauth2_scheme)):
    result = await verify_token(token)
    return result


@app.get('/circuitbreak', status_code=200)
@circuit_breaker
def circuit_breaker_endpoint(adapter: ExternalAPIAdapter = Depends()):
    try:
        return adapter.external_api_call()
    except pybreaker.CircuitBreakerError as cb_error:
        logger.error(f'CIRCUIT BREAKER ERROR: {cb_error}')
        raise HTTPException(status_code=503, detail="Circuit Breaker open")
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail="General application error")
