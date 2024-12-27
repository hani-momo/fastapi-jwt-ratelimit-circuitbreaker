'''
Tests module
'''
import time
from unittest.mock import patch, MagicMock

import pybreaker

from fastapi.testclient import TestClient

from config import ACCESS_TOKEN_EXPIRE_MINUTES
from main import app, serviceRegistry, ExternalAPIAdapter, SERVICE_NAME_EXTERNAL_API_ADAPTER


client = TestClient(app)


def test_root():
    response = client.get('/')
    assert response.status_code == 200

def test_register_new_user():
    response = client.post(
        '/register',
        json={'username': 'newusername', 'password': 'newpassword'},
    )
    assert response.status_code == 201

def test_register_with_existing_username():
    for _ in range(2):
        response = client.post(
            '/register',
            json={'username': 'testusername', 'password': 'testpassword'},
        )
    assert response.status_code == 400

def test_login_with_bad_token():
    response = client.get(
        '/protected',
        headers={'Authorization': 'Bearer invalid_token'}
    )
    assert response.status_code == 401

def test_expired_token():
    client.post(
        '/register',
        json={'username': 'testusername', 'password': 'testpassword'},
    )
    login_response = client.post(
        '/login', 
        data={'username': 'testusername', 'password': 'testpassword'})
    assert login_response.status_code == 200
    access_token = login_response.json()['access_token']

    time.sleep((ACCESS_TOKEN_EXPIRE_MINUTES*60) + 1)

    response = client.get('/protected', headers={'Authorization': f'Bearer {access_token}'})
    
    assert response.status_code == 401

def test_rate_limiter():
    for _ in range(4):
        response = client.post(
            '/login', 
            data={'username': 'testusername', 'password': 'testpassword'})
        if response.status_code ==429:
            break
        time.sleep(1)
    assert response.status_code == 429

def test_circuit_breaker_when_service_is_not_available():
    mock_external_api_adapter = MagicMock(spec=ExternalAPIAdapter)
    serviceRegistry.registerService(SERVICE_NAME_EXTERNAL_API_ADAPTER, mock_external_api_adapter)
    mock_external_api_adapter.external_api_call.return_value = False

    response = client.get('/circuitbreak')
    assert response.status_code == 503

def test_circuit_breaker_when_service_failed():
    mock_external_api_adapter = MagicMock(spec=ExternalAPIAdapter)
    serviceRegistry.registerService(SERVICE_NAME_EXTERNAL_API_ADAPTER, mock_external_api_adapter)
    mock_external_api_adapter.external_api_call.return_value = True

    for _ in range(5):
        response = client.get('/circuitbreak')
        assert response.status_code == 200

    mock_external_api_adapter.external_api_call.return_value = False
    try:
        for _ in range(5):
            response = client.get('/circuitbreak')
    except pybreaker.CircuitBreakerError:
        assert True
