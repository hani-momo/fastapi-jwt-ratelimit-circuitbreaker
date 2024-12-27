'''
Constants for main
'''

SECRET_KEY = 'efe06c37d11a0fb2aa2979ab564dfb165c286a196522ce2d0d42d67c0d420a58'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 0.01 # can be set to 0.1 for quick testing


'''
Configurations authentication and token
'''
key = 'secret'

from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

import jwt
encoded = jwt.encode({'some': 'payload'}, key, ALGORITHM)
jwt.decode(encoded, key, algorithms=['HS256'])
