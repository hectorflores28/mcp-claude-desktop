import pytest
from unittest.mock import Mock, patch
from app.core.cache import ClaudeCache

@pytest.fixture
def cache():
    with patch('redis.Redis') as mock_redis:
        cache = ClaudeCache()
        cache.redis_client = Mock()
        yield cache

def test_generate_key(cache):
    """Test que verifica la generación de claves de caché"""
    data = {"prompt": "test", "model": "claude-3"}
    key = cache._generate_key("response", data)
    assert key.startswith("claude:response:")
    assert len(key) > 20  # Verificar que el hash se generó

def test_cache_response(cache):
    """Test que verifica el almacenamiento de respuestas en caché"""
    prompt = "test prompt"
    response = {"text": "test response"}
    model = "claude-3"
    
    cache.cache_response(prompt, response, model)
    
    cache.redis_client.setex.assert_called_once()
    args = cache.redis_client.setex.call_args[0]
    assert args[0].startswith("claude:response:")
    assert args[1] == 3600  # TTL por defecto
    assert isinstance(args[2], str)  # Verificar que la respuesta se serializó

def test_get_cached_response(cache):
    """Test que verifica la recuperación de respuestas cacheadas"""
    prompt = "test prompt"
    model = "claude-3"
    cached_response = {"text": "cached response"}
    
    cache.redis_client.get.return_value = '{"text": "cached response"}'
    
    result = cache.get_cached_response(prompt, model)
    assert result == cached_response
    cache.redis_client.get.assert_called_once()

def test_get_cached_response_miss(cache):
    """Test que verifica el comportamiento cuando no hay caché"""
    prompt = "test prompt"
    model = "claude-3"
    
    cache.redis_client.get.return_value = None
    
    result = cache.get_cached_response(prompt, model)
    assert result is None

def test_cache_search_results(cache):
    """Test que verifica el almacenamiento de resultados de búsqueda"""
    query = "test query"
    results = {"results": ["result1", "result2"]}
    
    cache.cache_search_results(query, results)
    
    cache.redis_client.setex.assert_called_once()
    args = cache.redis_client.setex.call_args[0]
    assert args[0].startswith("claude:search:")
    assert args[1] == 3600  # TTL por defecto
    assert isinstance(args[2], str)  # Verificar que los resultados se serializaron

def test_get_cached_search(cache):
    """Test que verifica la recuperación de resultados de búsqueda cacheados"""
    query = "test query"
    cached_results = {"results": ["result1", "result2"]}
    
    cache.redis_client.get.return_value = '{"results": ["result1", "result2"]}'
    
    result = cache.get_cached_search(query)
    assert result == cached_results
    cache.redis_client.get.assert_called_once()

def test_invalidate_cache(cache):
    """Test que verifica la invalidación de entradas específicas del caché"""
    data = {"prompt": "test"}
    
    cache.invalidate_cache("response", data)
    
    cache.redis_client.delete.assert_called_once()
    args = cache.redis_client.delete.call_args[0]
    assert args[0].startswith("claude:response:")

def test_clear_all_cache(cache):
    """Test que verifica la limpieza completa del caché"""
    cache.redis_client.keys.return_value = ["claude:key1", "claude:key2"]
    
    cache.clear_all_cache()
    
    cache.redis_client.keys.assert_called_once_with("claude:*")
    cache.redis_client.delete.assert_called_once_with("claude:key1", "claude:key2") 