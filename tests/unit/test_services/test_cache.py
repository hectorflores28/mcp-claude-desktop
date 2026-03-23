import pytest
import time
from app.services.cache import CacheService
from app.core.exceptions import CacheError

class TestCacheService:
    """Pruebas unitarias para el servicio de caché"""
    
    @pytest.fixture
    def cache_service(self):
        """Fixture para el servicio de caché"""
        return CacheService()
    
    def test_set_and_get(self, cache_service):
        """Prueba almacenar y obtener un valor"""
        # Almacenar valor
        cache_service.set("test_key", "test_value")
        
        # Obtener valor
        value = cache_service.get("test_key")
        
        # Verificar valor
        assert value == "test_value"
    
    def test_get_nonexistent(self, cache_service):
        """Prueba obtener un valor que no existe"""
        value = cache_service.get("nonexistent_key")
        assert value is None
    
    def test_delete(self, cache_service):
        """Prueba eliminar un valor"""
        # Almacenar valor
        cache_service.set("test_key", "test_value")
        
        # Eliminar valor
        cache_service.delete("test_key")
        
        # Verificar que no existe
        value = cache_service.get("test_key")
        assert value is None
    
    def test_clear(self, cache_service):
        """Prueba limpiar toda la caché"""
        # Almacenar valores
        cache_service.set("key1", "value1")
        cache_service.set("key2", "value2")
        
        # Limpiar caché
        cache_service.clear()
        
        # Verificar que no hay valores
        assert cache_service.get_size() == 0
    
    def test_ttl(self, cache_service):
        """Prueba el tiempo de vida de los valores"""
        # Almacenar valor con TTL corto
        cache_service.set("test_key", "test_value", ttl=1)
        
        # Verificar que existe
        assert cache_service.get("test_key") == "test_value"
        
        # Esperar a que expire
        time.sleep(1.1)
        
        # Verificar que ya no existe
        assert cache_service.get("test_key") is None
    
    def test_get_size(self, cache_service):
        """Prueba obtener el tamaño de la caché"""
        # Almacenar valores
        cache_service.set("key1", "value1")
        cache_service.set("key2", "value2")
        
        # Verificar tamaño
        assert cache_service.get_size() == 2
        
        # Eliminar un valor
        cache_service.delete("key1")
        
        # Verificar nuevo tamaño
        assert cache_service.get_size() == 1
    
    def test_get_stats(self, cache_service):
        """Prueba obtener estadísticas de la caché"""
        # Almacenar valores
        cache_service.set("key1", "value1")
        cache_service.set("key2", "value2")
        
        # Obtener estadísticas
        stats = cache_service.get_stats()
        
        # Verificar estadísticas
        assert stats["size"] == 2
        assert "default_ttl" in stats
    
    def test_error_handling(self, cache_service):
        """Prueba el manejo de errores"""
        # Simular error al almacenar
        with pytest.raises(CacheError) as exc_info:
            cache_service.set(None, "value")
        
        assert "Error al almacenar valor en la caché" in str(exc_info.value)
        
        # Simular error al obtener
        with pytest.raises(CacheError) as exc_info:
            cache_service.get(None)
        
        assert "Error al obtener valor de la caché" in str(exc_info.value) 