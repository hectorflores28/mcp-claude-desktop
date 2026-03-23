import pytest
import requests
import json
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "tu-clave-secreta")

@pytest.fixture
def headers():
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

def test_connection_basic():
    """Prueba la conexión básica al servidor MCP"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"

def test_authentication():
    """Prueba la autenticación con API Key"""
    response = requests.get(
        f"{BASE_URL}/api/mcp/status",
        headers=headers()
    )
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "status" in data

def test_mcp_basic_operation():
    """Prueba una operación MCP básica"""
    payload = {
        "operation": "test",
        "parameters": {}
    }
    response = requests.post(
        f"{BASE_URL}/api/mcp/execute",
        headers=headers(),
        json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert "result" in data

def test_cache_system():
    """Prueba el sistema de caché"""
    # Primera solicitud (debe guardar en caché)
    response1 = requests.get(
        f"{BASE_URL}/api/mcp/status",
        headers=headers()
    )
    assert response1.status_code == 200
    
    # Segunda solicitud (debe venir de caché)
    response2 = requests.get(
        f"{BASE_URL}/api/mcp/status",
        headers=headers()
    )
    assert response2.status_code == 200
    
    # Verificar que las respuestas son idénticas
    assert response1.json() == response2.json()

def test_logging():
    """Prueba que los logs se están generando correctamente"""
    # Realizar una operación que genere logs
    response = requests.get(
        f"{BASE_URL}/api/mcp/operations",
        headers=headers()
    )
    assert response.status_code == 200
    
    # Verificar que existe el archivo de logs
    log_file = os.path.join(os.getenv("LOG_DIR", "logs"), "mcp.log")
    assert os.path.exists(log_file)

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 