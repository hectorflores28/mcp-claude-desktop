import pytest
from app.core.cache import cache
from app.core.blacklist import blacklist
import time

@pytest.mark.asyncio
async def test_cache_integration():
    """
    Test de integración del sistema de caché
    """
    # Test de set y get
    test_data = {"test": "data"}
    await cache.set("test_key", test_data, ttl=1)
    cached_data = await cache.get("test_key")
    assert cached_data == test_data
    
    # Test de expiración
    time.sleep(1.1)
    expired_data = await cache.get("test_key")
    assert expired_data is None
    
    # Test de delete
    await cache.set("test_key", test_data)
    await cache.delete("test_key")
    deleted_data = await cache.get("test_key")
    assert deleted_data is None
    
    # Test de clear
    await cache.set("key1", "value1")
    await cache.set("key2", "value2")
    await cache.clear()
    assert await cache.get("key1") is None
    assert await cache.get("key2") is None

@pytest.mark.asyncio
async def test_blacklist_integration():
    """
    Test de integración de la lista negra de tokens
    """
    # Test de add_to_blacklist
    test_token = "test_token"
    await blacklist.add_to_blacklist(test_token, expires_in=1)
    assert await blacklist.is_blacklisted(test_token) is True
    
    # Test de expiración
    time.sleep(1.1)
    assert await blacklist.is_blacklisted(test_token) is False
    
    # Test de remove_from_blacklist
    await blacklist.add_to_blacklist(test_token)
    await blacklist.remove_from_blacklist(test_token)
    assert await blacklist.is_blacklisted(test_token) is False
    
    # Test de clear_blacklist
    await blacklist.add_to_blacklist("token1")
    await blacklist.add_to_blacklist("token2")
    await blacklist.clear_blacklist()
    assert await blacklist.is_blacklisted("token1") is False
    assert await blacklist.is_blacklisted("token2") is False

@pytest.mark.asyncio
async def test_cache_and_blacklist_integration():
    """
    Test de integración entre caché y lista negra
    """
    # Test de caché con datos de blacklist
    test_token = "test_token"
    await blacklist.add_to_blacklist(test_token)
    
    # Verificar que el token está en la lista negra usando el caché
    assert await cache.exists(f"{blacklist.prefix}{test_token}") is True
    
    # Limpiar blacklist y verificar caché
    await blacklist.clear_blacklist()
    assert await cache.exists(f"{blacklist.prefix}{test_token}") is False 