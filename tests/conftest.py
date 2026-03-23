"""
Configuración de pytest y fixtures comunes.

Este módulo proporciona la configuración base para las pruebas y fixtures
que serán utilizados en todo el proyecto.
"""

import pytest
from fastapi.testclient import TestClient
from typing import Generator, Dict, Any
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path para importaciones
sys.path.append(str(Path(__file__).parent.parent))

from app.main import app
from app.core.config import settings
from app.core.plugins import plugin_manager
from app.services.mcp_service import MCPService

@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """
    Fixture que proporciona un cliente de prueba para FastAPI.
    
    Yields:
        TestClient: Cliente de prueba configurado
    """
    with TestClient(app) as client:
        yield client

@pytest.fixture
def mcp_service() -> MCPService:
    """
    Fixture que proporciona una instancia del servicio MCP.
    
    Returns:
        MCPService: Instancia del servicio MCP
    """
    return MCPService()

@pytest.fixture
def test_settings() -> Dict[str, Any]:
    """
    Fixture que proporciona configuración de prueba.
    
    Returns:
        Dict[str, Any]: Configuración de prueba
    """
    return {
        "ENVIRONMENT": "test",
        "DEBUG": True,
        "LOG_LEVEL": "DEBUG",
        "PLUGINS_ENABLED": True,
        "PLUGIN_DIR": "tests/plugins",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": 6379,
        "REDIS_DB": 1,
        "API_KEY": "test_api_key",
        "JWT_SECRET_KEY": "test_secret_key",
        "JWT_ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": 30
    }

@pytest.fixture(autouse=True)
def setup_test_env(test_settings: Dict[str, Any]) -> None:
    """
    Fixture que configura el entorno de prueba.
    
    Args:
        test_settings: Configuración de prueba
    """
    # Guardar configuración original
    original_settings = {key: getattr(settings, key) for key in test_settings}
    
    # Aplicar configuración de prueba
    for key, value in test_settings.items():
        setattr(settings, key, value)
    
    yield
    
    # Restaurar configuración original
    for key, value in original_settings.items():
        setattr(settings, key, value)

@pytest.fixture(autouse=True)
def setup_test_plugins() -> None:
    """
    Fixture que configura los plugins para pruebas.
    """
    # Crear directorio de plugins de prueba si no existe
    os.makedirs(settings.PLUGIN_DIR, exist_ok=True)
    
    # Cargar plugins
    plugin_manager.load_plugins()
    
    yield
    
    # Limpiar plugins
    plugin_manager.shutdown()

@pytest.fixture
def test_env():
    """Fixture para variables de entorno de prueba"""
    os.environ["CLAUDE_API_KEY"] = "test_claude_key"
    os.environ["BRAVE_SEARCH_API_KEY"] = "test_brave_key"
    return {
        "CLAUDE_API_KEY": "test_claude_key",
        "BRAVE_SEARCH_API_KEY": "test_brave_key"
    }

@pytest.fixture
def test_data_dir():
    """Fixture para directorio de datos de prueba"""
    test_dir = Path("tests/data")
    test_dir.mkdir(exist_ok=True)
    return test_dir

@pytest.fixture
def test_log_dir():
    """Fixture para directorio de logs de prueba"""
    test_dir = Path("tests/logs")
    test_dir.mkdir(exist_ok=True)
    return test_dir

@pytest.fixture
def mock_claude_response():
    """Fixture para respuestas simuladas de Claude"""
    return {
        "content": "Test response from Claude",
        "model": settings.CLAUDE_MODEL,
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }

@pytest.fixture
def mock_search_response():
    """Fixture para respuestas simuladas de búsqueda"""
    return {
        "results": [
            {
                "title": "Test Result",
                "url": "https://test.com",
                "snippet": "Test snippet"
            }
        ]
    } 