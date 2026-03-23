"""
Pruebas de integración para los endpoints de la API.

Este módulo contiene las pruebas de integración para los endpoints
de la API, incluyendo autenticación, operaciones MCP y plugins.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
import jwt
from datetime import datetime, timedelta

# Cliente de prueba
client = TestClient(app)

def create_test_token():
    """
    Crea un token JWT para pruebas
    """
    payload = {
        "sub": "test_user",
        "exp": datetime.utcnow() + timedelta(minutes=30),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

@pytest.fixture
def auth_headers():
    """
    Fixture para headers de autenticación
    """
    token = create_test_token()
    return {"Authorization": f"Bearer {token}"}

def test_health_check():
    """
    Test del endpoint de health check
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "services" in data

def test_status_endpoint():
    """
    Test del endpoint de status
    """
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "environment" in data
    assert "services" in data

def test_auth_token_endpoint():
    """
    Test del endpoint de generación de token
    """
    response = client.post(
        "/api/v1/auth/token",
        json={"username": "test_user", "password": "test_password"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

def test_auth_token_invalid_credentials():
    """
    Test del endpoint de token con credenciales inválidas
    """
    response = client.post(
        "/api/v1/auth/token",
        json={"username": "invalid", "password": "invalid"}
    )
    assert response.status_code == 401

def test_protected_endpoint_with_token(auth_headers):
    """
    Test de acceso a endpoint protegido con token válido
    """
    response = client.get("/api/v1/mcp/status", headers=auth_headers)
    assert response.status_code == 200

def test_protected_endpoint_without_token():
    """
    Test de acceso a endpoint protegido sin token
    """
    response = client.get("/api/v1/mcp/status")
    assert response.status_code == 401

def test_rate_limit():
    """
    Test del rate limiting
    """
    # Realizar múltiples peticiones para alcanzar el límite
    for _ in range(settings.RATE_LIMIT_MAX_REQUESTS + 1):
        response = client.get("/health")
    
    # La última petición debería ser rechazada
    assert response.status_code == 429

def test_auth_refresh_token(auth_headers):
    """
    Test del endpoint de refresh token
    """
    response = client.post(
        "/api/v1/auth/refresh",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

def test_auth_revoke_token(auth_headers):
    """
    Test del endpoint de revocación de token
    """
    response = client.post(
        "/api/v1/auth/revoke",
        headers=auth_headers
    )
    assert response.status_code == 200
    
    # Intentar usar el token revocado
    response = client.get("/api/v1/mcp/status", headers=auth_headers)
    assert response.status_code == 401 