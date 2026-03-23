import pytest
from unittest.mock import patch, MagicMock
from app.services.claude_client import ClaudeClient
from app.core.config import settings

class TestClaudeClient:
    """Pruebas unitarias para el cliente de Claude"""
    
    @pytest.fixture
    def claude_client(self):
        """Fixture para el cliente de Claude"""
        return ClaudeClient()
    
    def test_generate_text(self, claude_client, mock_claude_response):
        """Prueba la generación de texto"""
        with patch('app.services.claude_client.requests.post') as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_claude_response
            )
            
            response = claude_client.generate_text(
                prompt="Test prompt",
                max_tokens=100,
                temperature=0.7
            )
            
            assert response["content"] == mock_claude_response["content"]
            assert response["model"] == settings.CLAUDE_MODEL
            assert "usage" in response
    
    def test_analyze_text(self, claude_client, mock_claude_response):
        """Prueba el análisis de texto"""
        with patch('app.services.claude_client.requests.post') as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_claude_response
            )
            
            response = claude_client.analyze_text(
                text="Test text",
                analysis_type="sentiment"
            )
            
            assert response["content"] == mock_claude_response["content"]
            assert response["model"] == settings.CLAUDE_MODEL
    
    def test_error_handling(self, claude_client):
        """Prueba el manejo de errores"""
        with patch('app.services.claude_client.requests.post') as mock_post:
            mock_post.side_effect = Exception("API Error")
            
            with pytest.raises(Exception) as exc_info:
                claude_client.generate_text("Test prompt")
            
            assert str(exc_info.value) == "API Error"
    
    def test_rate_limit_handling(self, claude_client):
        """Prueba el manejo de límites de tasa"""
        with patch('app.services.claude_client.requests.post') as mock_post:
            mock_post.return_value = MagicMock(
                status_code=429,
                json=lambda: {"error": "Rate limit exceeded"}
            )
            
            with pytest.raises(Exception) as exc_info:
                claude_client.generate_text("Test prompt")
            
            assert "Rate limit exceeded" in str(exc_info.value) 