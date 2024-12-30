'''
Tests module
'''
import time
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from fastapi.testclient import TestClient

from config import ACCESS_TOKEN_EXPIRE_MINUTES
from main import app, ExternalAPIAdapter

import pybreaker


client = TestClient(app)

@pytest.fixture
def mock_adapter():
    adapter = MagicMock(spec=ExternalAPIAdapter)
    app.dependency_overrides[ExternalAPIAdapter] = lambda: adapter
    return adapter

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
    for _ in range(3):
        response = client.post(
            '/login', 
            data={'username': 'testusername', 'password': 'testpassword'})
        if response.status_code == 429:
            break
        time.sleep(1)
    assert response.status_code == 429

def test_circuit_breaker_success(mock_adapter):
    response = client.get('/circuitbreak')
    assert response.status_code == 200

def test_circuit_breaker_fail_max_reached_and_reset(mock_adapter):
    mock_adapter.external_api_call.side_effect = [
        HTTPException(status_code=500), HTTPException(status_code=500), HTTPException(status_code=500),
        HTTPException(status_code=503), 
        'hello']
    try:
        for _ in range(3):
            response = client.get('/circuitbreak')     
    except Exception as e:            
        assert response.status_code == 500

    try:
        response = client.get('/circuitbreak')
        assert False
    except pybreaker.CircuitBreakerError:
        assert True

    time.sleep(6)
    mock_adapter.external_api_call.return_value = 'hello'
    for _ in range(10):
        time.sleep(1)
        try:
            response = client.get('/circuitbreak')
            assert True
            return
        except Exception:
            pass
    return False

def test_service_returns_io_error(mock_adapter):
    mock_adapter.external_api_call.side_effect = IOError()
    response = client.get('/circuitbreak')
    assert response.status_code == 500

def test_service_returns_timeout(mock_adapter):
    mock_adapter.external_api_call.side_effect = TimeoutError()
    response = client.get('/circuitbreak')
    assert response.status_code == 500
