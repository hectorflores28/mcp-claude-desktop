"""
Tests de seguridad para el servidor MCP-Claude.

Este módulo contiene pruebas de seguridad para evaluar la protección
del sistema contra diferentes tipos de ataques.
"""

import pytest
import jwt
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.blacklist import blacklist

client = TestClient(app)

@pytest.mark.security
def test_jwt_token_validation():
    """
    Test de validación de tokens JWT.
    """
    # Token inválido
    response = client.get(
        "/api/v1/mcp/status",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    
    # Token expirado
    expired_token = jwt.encode(
        {"exp": 0},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    response = client.get(
        "/api/v1/mcp/status",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401
    
    # Token en lista negra
    token = jwt.encode(
        {"sub": "test"},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    blacklist.add_to_blacklist(token)
    response = client.get(
        "/api/v1/mcp/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401

@pytest.mark.security
def test_api_key_validation():
    """
    Test de validación de API Key.
    """
    # API Key inválida
    response = client.get(
        "/api/v1/mcp/status",
        headers={"X-API-Key": "invalid_key"}
    )
    assert response.status_code == 401
    
    # API Key correcta
    response = client.get(
        "/api/v1/mcp/status",
        headers={"X-API-Key": settings.API_KEY}
    )
    assert response.status_code == 200

@pytest.mark.security
def test_rate_limiting():
    """
    Test de límites de tasa.
    """
    # Realizar múltiples solicitudes rápidas
    for _ in range(settings.RATE_LIMIT_MAX_REQUESTS + 1):
        response = client.get(
            "/api/v1/mcp/status",
            headers={"X-API-Key": settings.API_KEY}
        )
    
    # La última solicitud debería ser rechazada
    assert response.status_code == 429

@pytest.mark.security
def test_cors_protection():
    """
    Test de protección CORS.
    """
    # Origen no permitido
    response = client.get(
        "/api/v1/mcp/status",
        headers={
            "Origin": "http://malicious-site.com",
            "X-API-Key": settings.API_KEY
        }
    )
    assert "Access-Control-Allow-Origin" not in response.headers
    
    # Origen permitido
    response = client.get(
        "/api/v1/mcp/status",
        headers={
            "Origin": settings.CORS_ORIGINS.split(",")[0],
            "X-API-Key": settings.API_KEY
        }
    )
    assert "Access-Control-Allow-Origin" in response.headers

@pytest.mark.security
def test_sql_injection_protection():
    """
    Test de protección contra inyección SQL.
    """
    # Intentar inyección SQL en parámetros
    response = client.get(
        "/api/v1/mcp/status",
        params={"id": "1; DROP TABLE users;"},
        headers={"X-API-Key": settings.API_KEY}
    )
    assert response.status_code == 400

@pytest.mark.security
def test_xss_protection():
    """
    Test de protección contra XSS.
    """
    # Intentar inyección XSS en parámetros
    response = client.get(
        "/api/v1/mcp/status",
        params={"query": "<script>alert('xss')</script>"},
        headers={"X-API-Key": settings.API_KEY}
    )
    assert response.status_code == 400 