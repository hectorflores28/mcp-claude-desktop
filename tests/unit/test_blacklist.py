import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from app.core.blacklist import TokenBlacklist
from app.core.cache import cache

@pytest.fixture
def mock_cache():
    with patch("app.core.cache.cache") as mock:
        yield mock

@pytest.fixture
def blacklist(mock_cache):
    return TokenBlacklist()

@pytest.mark.asyncio
async def test_add_to_blacklist(blacklist, mock_cache):
    # Configurar mock
    mock_cache.set.return_value = True
    
    # Probar add_to_blacklist
    result = await blacklist.add_to_blacklist("test_token", expires_in=3600)
    assert result is True
    mock_cache.set.assert_called_once()

@pytest.mark.asyncio
async def test_is_blacklisted(blacklist, mock_cache):
    # Configurar mock
    mock_cache.exists.return_value = True
    
    # Probar is_blacklisted
    result = await blacklist.is_blacklisted("test_token")
    assert result is True
    mock_cache.exists.assert_called_once()

@pytest.mark.asyncio
async def test_remove_from_blacklist(blacklist, mock_cache):
    # Configurar mock
    mock_cache.delete.return_value = True
    
    # Probar remove_from_blacklist
    result = await blacklist.remove_from_blacklist("test_token")
    assert result is True
    mock_cache.delete.assert_called_once()

@pytest.mark.asyncio
async def test_clear_blacklist(blacklist, mock_cache):
    # Configurar mock
    mock_cache.redis_client.keys.return_value = ["key1", "key2"]
    mock_cache.redis_client.delete.return_value = 2
    
    # Probar clear_blacklist
    result = await blacklist.clear_blacklist()
    assert result is True
    mock_cache.redis_client.delete.assert_called_once()

@pytest.mark.asyncio
async def test_add_to_blacklist_with_token_expiry(blacklist, mock_cache):
    # Configurar mock
    mock_cache.set.return_value = True
    
    # Simular token con expiración
    with patch("app.core.blacklist.decode_token") as mock_decode:
        mock_decode.return_value = {
            "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp())
        }
        
        # Probar add_to_blacklist sin expires_in
        result = await blacklist.add_to_blacklist("test_token")
        assert result is True
        mock_cache.set.assert_called_once() 