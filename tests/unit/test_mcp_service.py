"""
Pruebas unitarias para el servicio MCP.

Este módulo contiene las pruebas unitarias para el servicio MCP,
incluyendo pruebas de caché, rate limiting y operaciones básicas.
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
from app.services.mcp_service import MCPService
from app.schemas.mcp import MCPRequest, MCPResponse, MCPError, MCPStatus, MCPOperation
from datetime import datetime
from app.core.cache import RedisCache
from app.core.logging import LogManager
from app.core.plugins import plugin_manager

@pytest.fixture
def mcp_service():
    """Fixture para crear una instancia de MCPService con dependencias mockeadas"""
    with patch('app.services.mcp_service.RedisCache') as mock_cache:
        with patch('app.services.mcp_service.LogManager') as mock_logger:
            service = MCPService()
            service.cache = mock_cache.return_value
            service.logger = mock_logger
            yield service

@pytest.fixture
def valid_request():
    return MCPRequest(
        version="1.1",
        method="status",
        parameters={}
    )

@pytest.fixture
def execute_request():
    return MCPRequest(
        version="1.1",
        method="execute",
        parameters={
            "tool": "buscar_en_brave",
            "params": {
                "query": "test query",
                "num_results": 3
            }
        }
    )

class TestMCPService:
    
    async def test_get_status(self, mcp_service):
        """Test que verifica que get_status devuelve un objeto MCPStatus válido"""
        status = await mcp_service.get_status()
        
        assert isinstance(status, MCPStatus)
        assert status.version == "1.1"
        assert "features" in status.dict()
        assert "resource_types" in status.dict()
        assert "access_levels" in status.dict()
        assert "resources" in status.dict()
        assert "tools" in status.dict()
        assert isinstance(status.timestamp, datetime)
    
    async def test_validate_request_valid(self, mcp_service, valid_request):
        """Test que verifica que una solicitud válida pasa la validación"""
        result = await mcp_service.validate_request(valid_request)
        assert result is None  # None significa que no hay errores
    
    async def test_validate_request_invalid_version(self, mcp_service):
        """Test que verifica que una solicitud con versión inválida falla la validación"""
        invalid_request = MCPRequest(
            version="0.9",  # Versión no soportada
            method="status",
            parameters={}
        )
        
        result = await mcp_service.validate_request(invalid_request)
        assert isinstance(result, MCPError)
        assert result.code == 400
        assert "versión no soportada" in result.message.lower()
    
    async def test_validate_request_invalid_method(self, mcp_service):
        """Test que verifica que una solicitud con método inválido falla la validación"""
        invalid_request = MCPRequest(
            version="1.1",
            method="invalid_method",  # Método no soportado
            parameters={}
        )
        
        result = await mcp_service.validate_request(invalid_request)
        assert isinstance(result, MCPError)
        assert result.code == 400
        assert "método no soportado" in result.message.lower()
    
    @patch('app.services.mcp_service.MCPService._check_rate_limit')
    async def test_process_request_status(self, mock_rate_limit, mcp_service, valid_request):
        """Test que verifica el procesamiento de una solicitud de estado"""
        mock_rate_limit.return_value = None  # No hay error de rate limit
        
        response = await mcp_service.process_request(valid_request)
        
        assert isinstance(response, MCPResponse)
        assert response.version == "1.1"
        assert response.method == "status"
        assert "status" in response.result
        assert response.error is None
    
    @patch('app.services.mcp_service.MCPService._check_rate_limit')
    @patch('app.services.mcp_service.MCPService._execute_tool')
    async def test_process_request_execute(self, mock_execute_tool, mock_rate_limit, mcp_service, execute_request):
        """Test que verifica el procesamiento de una solicitud de ejecución"""
        mock_rate_limit.return_value = None  # No hay error de rate limit
        mock_execute_tool.return_value = {"results": ["result1", "result2"]}
        
        response = await mcp_service.process_request(execute_request)
        
        assert isinstance(response, MCPResponse)
        assert response.version == "1.1"
        assert response.method == "execute"
        assert "results" in response.result
        assert response.error is None
        assert response.execution_time > 0
    
    async def test_get_recent_operations(self, mcp_service):
        """Test que verifica la obtención de operaciones recientes"""
        # Añadir algunas operaciones
        mcp_service.operations = [
            MCPOperation(
                method="status",
                parameters={},
                timestamp=datetime.now(),
                status="success",
                execution_time=0.1
            ),
            MCPOperation(
                method="execute",
                parameters={"tool": "test"},
                timestamp=datetime.now(),
                status="success",
                execution_time=0.2
            )
        ]
        
        operations = mcp_service.get_recent_operations(limit=1)
        
        assert len(operations) == 1
        assert operations[0].method == "execute"  # La más reciente

@pytest.mark.asyncio
async def test_get_status_with_cache(mcp_service):
    """
    Prueba la obtención del estado con caché.
    
    Args:
        mcp_service: Fixture del servicio MCP
    """
    # Configurar caché
    with patch("app.services.mcp_service.redis_client") as mock_redis:
        mock_redis.get.return_value = '{"status": "ok", "version": "1.0.0"}'
        
        # Obtener estado
        status = await mcp_service.get_status()
        
        # Verificar resultado
        assert status["status"] == "ok"
        assert status["version"] == "1.0.0"
        
        # Verificar que se usó el caché
        mock_redis.get.assert_called_once()

@pytest.mark.asyncio
async def test_get_status_without_cache(mcp_service):
    """
    Prueba la obtención del estado sin caché.
    
    Args:
        mcp_service: Fixture del servicio MCP
    """
    # Configurar caché vacío
    with patch("app.services.mcp_service.redis_client") as mock_redis:
        mock_redis.get.return_value = None
        
        # Obtener estado
        status = await mcp_service.get_status()
        
        # Verificar resultado
        assert status["status"] == "ok"
        assert "version" in status
        
        # Verificar que se intentó usar el caché
        mock_redis.get.assert_called_once()

@pytest.mark.asyncio
async def test_check_rate_limit(mcp_service):
    """
    Prueba la verificación del rate limit.
    
    Args:
        mcp_service: Fixture del servicio MCP
    """
    # Configurar Redis
    with patch("app.services.mcp_service.redis_client") as mock_redis:
        mock_redis.incr.return_value = 1
        
        # Verificar rate limit
        result = await mcp_service.check_rate_limit("test_key")
        
        # Verificar resultado
        assert result is True
        mock_redis.incr.assert_called_once()

@pytest.mark.asyncio
async def test_check_rate_limit_exceeded(mcp_service):
    """
    Prueba la verificación del rate limit cuando se excede.
    
    Args:
        mcp_service: Fixture del servicio MCP
    """
    # Configurar Redis
    with patch("app.services.mcp_service.redis_client") as mock_redis:
        mock_redis.incr.return_value = 101  # Excede el límite
        
        # Verificar rate limit
        result = await mcp_service.check_rate_limit("test_key")
        
        # Verificar resultado
        assert result is False
        mock_redis.incr.assert_called_once()

@pytest.mark.asyncio
async def test_execute_operation_with_plugins(mcp_service):
    """
    Prueba la ejecución de operaciones con plugins.
    
    Args:
        mcp_service: Fixture del servicio MCP
    """
    # Configurar plugin
    mock_plugin = Mock()
    mock_plugin.enabled = True
    mock_plugin.before_execute = Mock(return_value=None)
    mock_plugin.after_execute = Mock(return_value=None)
    
    plugin_manager.plugins["test_plugin"] = mock_plugin
    
    # Ejecutar operación
    result = await mcp_service.execute_operation("test_op", {"param": "value"})
    
    # Verificar que se llamaron los hooks
    mock_plugin.before_execute.assert_called_once()
    mock_plugin.after_execute.assert_called_once()
    
    # Verificar resultado
    assert result is not None

@pytest.mark.asyncio
async def test_execute_operation_with_error(mcp_service):
    """
    Prueba la ejecución de operaciones con error.
    
    Args:
        mcp_service: Fixture del servicio MCP
    """
    # Configurar plugin
    mock_plugin = Mock()
    mock_plugin.enabled = True
    mock_plugin.on_error = Mock(return_value=None)
    
    plugin_manager.plugins["test_plugin"] = mock_plugin
    
    # Ejecutar operación que genera error
    with pytest.raises(Exception):
        await mcp_service.execute_operation("invalid_op", {})
    
    # Verificar que se llamó el hook de error
    mock_plugin.on_error.assert_called_once() 