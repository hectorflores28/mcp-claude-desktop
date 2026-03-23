import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.schemas.mcp import MCPStatus, MCPOperation

client = TestClient(app)

@pytest.fixture
def mock_mcp_service():
    with patch("app.api.endpoints.mcp.mcp_service") as mock:
        yield mock

class TestMCPEndpoints:
    
    def test_mcp_status(self, mock_mcp_service):
        """Test que verifica el endpoint de estado MCP"""
        # Configurar el mock
        mock_status = MCPStatus(
            version="1.1",
            features=["resources", "tools"],
            resource_types=["filesystem", "claude"],
            access_levels=["read", "write"],
            resources={},
            tools={},
            timestamp="2024-04-07T12:00:00Z"
        )
        mock_mcp_service.get_status.return_value = mock_status
        
        # Llamar al endpoint
        response = client.get("/api/mcp/status")
        
        # Verificar la respuesta
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "1.1"
        assert "features" in data
        assert "resource_types" in data
        assert "access_levels" in data
        assert "resources" in data
        assert "tools" in data
        assert "timestamp" in data
    
    def test_mcp_execute(self, mock_mcp_service):
        """Test que verifica el endpoint de ejecución MCP"""
        # Configurar el mock
        mock_response = {
            "version": "1.1",
            "method": "execute",
            "result": {"results": ["result1", "result2"]},
            "error": None,
            "execution_time": 0.5
        }
        mock_mcp_service.process_request.return_value = mock_response
        
        # Llamar al endpoint
        request_data = {
            "version": "1.1",
            "method": "execute",
            "parameters": {
                "tool": "buscar_en_brave",
                "params": {
                    "query": "test query",
                    "num_results": 3
                }
            }
        }
        response = client.post("/api/mcp/execute", json=request_data)
        
        # Verificar la respuesta
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "1.1"
        assert data["method"] == "execute"
        assert "results" in data["result"]
        assert data["error"] is None
        assert "execution_time" in data
    
    def test_mcp_operations(self, mock_mcp_service):
        """Test que verifica el endpoint de operaciones recientes"""
        # Configurar el mock
        mock_operations = [
            MCPOperation(
                method="status",
                parameters={},
                timestamp="2024-04-07T12:00:00Z",
                status="success",
                execution_time=0.1
            ),
            MCPOperation(
                method="execute",
                parameters={"tool": "test"},
                timestamp="2024-04-07T12:01:00Z",
                status="success",
                execution_time=0.2
            )
        ]
        mock_mcp_service.get_recent_operations.return_value = mock_operations
        
        # Llamar al endpoint
        response = client.get("/api/mcp/operations?limit=2")
        
        # Verificar la respuesta
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["method"] == "execute"  # La más reciente
        assert data[1]["method"] == "status" 