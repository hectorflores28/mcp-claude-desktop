import pytest
from unittest.mock import Mock, patch
from app.core.cache import RedisCache
from app.core.config import settings

@pytest.fixture
def mock_redis():
    with patch("redis.Redis") as mock:
        yield mock

@pytest.fixture
def cache(mock_redis):
    return RedisCache()

@pytest.mark.asyncio
async def test_cache_set(cache, mock_redis):
    # Configurar mock
    mock_redis.return_value.setex.return_value = True
    
    # Probar set
    result = await cache.set("test_key", {"data": "test"})
    assert result is True
    mock_redis.return_value.setex.assert_called_once()

@pytest.mark.asyncio
async def test_cache_get(cache, mock_redis):
    # Configurar mock
    mock_redis.return_value.get.return_value = '{"data": "test"}'
    
    # Probar get
    result = await cache.get("test_key")
    assert result == {"data": "test"}
    mock_redis.return_value.get.assert_called_once()

@pytest.mark.asyncio
async def test_cache_delete(cache, mock_redis):
    # Configurar mock
    mock_redis.return_value.delete.return_value = 1
    
    # Probar delete
    result = await cache.delete("test_key")
    assert result is True
    mock_redis.return_value.delete.assert_called_once()

@pytest.mark.asyncio
async def test_cache_clear(cache, mock_redis):
    # Configurar mock
    mock_redis.return_value.keys.return_value = ["key1", "key2"]
    mock_redis.return_value.delete.return_value = 2
    
    # Probar clear
    result = await cache.clear()
    assert result is True
    mock_redis.return_value.delete.assert_called_once()

@pytest.mark.asyncio
async def test_cache_exists(cache, mock_redis):
    # Configurar mock
    mock_redis.return_value.exists.return_value = 1
    
    # Probar exists
    result = await cache.exists("test_key")
    assert result is True
    mock_redis.return_value.exists.assert_called_once() 