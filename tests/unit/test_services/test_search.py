import pytest
from unittest.mock import patch, MagicMock
from app.services.search import SearchService
from app.core.exceptions import SearchAPIError
from app.core.config import settings

class TestSearchService:
    """Pruebas unitarias para el servicio de búsqueda"""
    
    @pytest.fixture
    def search_service(self):
        """Fixture para el servicio de búsqueda"""
        return SearchService()
    
    def test_search(self, search_service, mock_search_response):
        """Prueba la búsqueda básica"""
        with patch('app.services.search.requests.get') as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_search_response
            )
            
            results = search_service.search("test query")
            
            assert len(results) == len(mock_search_response["results"])
            assert results[0]["title"] == mock_search_response["results"][0]["title"]
            assert results[0]["url"] == mock_search_response["results"][0]["url"]
            assert results[0]["snippet"] == mock_search_response["results"][0]["snippet"]
    
    def test_search_with_limit(self, search_service, mock_search_response):
        """Prueba la búsqueda con límite de resultados"""
        with patch('app.services.search.requests.get') as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_search_response
            )
            
            results = search_service.search("test query", limit=1)
            
            assert len(results) == 1
    
    def test_search_error(self, search_service):
        """Prueba el manejo de errores en la búsqueda"""
        with patch('app.services.search.requests.get') as mock_get:
            mock_get.side_effect = Exception("API Error")
            
            with pytest.raises(SearchAPIError) as exc_info:
                search_service.search("test query")
            
            assert "API Error" in str(exc_info.value)
    
    def test_search_rate_limit(self, search_service):
        """Prueba el manejo de límites de tasa"""
        with patch('app.services.search.requests.get') as mock_get:
            mock_get.return_value = MagicMock(
                status_code=429,
                json=lambda: {"error": "Rate limit exceeded"}
            )
            
            with pytest.raises(SearchAPIError) as exc_info:
                search_service.search("test query")
            
            assert "Rate limit exceeded" in str(exc_info.value)
    
    def test_search_invalid_response(self, search_service):
        """Prueba el manejo de respuestas inválidas"""
        with patch('app.services.search.requests.get') as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"invalid": "response"}
            )
            
            with pytest.raises(SearchAPIError) as exc_info:
                search_service.search("test query")
            
            assert "Invalid response format" in str(exc_info.value)
    
    def test_search_empty_query(self, search_service):
        """Prueba la búsqueda con consulta vacía"""
        with pytest.raises(SearchAPIError) as exc_info:
            search_service.search("")
        
        assert "Empty query" in str(exc_info.value)
    
    def test_search_api_key(self, search_service):
        """Prueba la validación de la clave API"""
        with patch('app.services.search.requests.get') as mock_get:
            mock_get.return_value = MagicMock(
                status_code=401,
                json=lambda: {"error": "Invalid API key"}
            )
            
            with pytest.raises(SearchAPIError) as exc_info:
                search_service.search("test query")
            
            assert "Invalid API key" in str(exc_info.value) 