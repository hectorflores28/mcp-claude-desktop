import time
from typing import Any, Optional, Dict
from app.core.config import settings
from app.core.exceptions import CacheError

class CacheService:
    """Servicio de caché para MCP-Claude"""
    
    def __init__(self):
        """Inicializa el servicio de caché"""
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._default_ttl = settings.CACHE_TTL
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtiene un valor de la caché
        
        Args:
            key: Clave del valor a obtener
            
        Returns:
            El valor almacenado o None si no existe o ha expirado
            
        Raises:
            CacheError: Si hay un error al acceder a la caché
        """
        try:
            if key not in self._cache:
                return None
                
            cache_entry = self._cache[key]
            if time.time() > cache_entry["expires_at"]:
                del self._cache[key]
                return None
                
            return cache_entry["value"]
        except Exception as e:
            raise CacheError(f"Error al obtener valor de la caché: {str(e)}")
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Almacena un valor en la caché
        
        Args:
            key: Clave para almacenar el valor
            value: Valor a almacenar
            ttl: Tiempo de vida en segundos (opcional)
            
        Raises:
            CacheError: Si hay un error al almacenar en la caché
        """
        try:
            expires_at = time.time() + (ttl if ttl is not None else self._default_ttl)
            self._cache[key] = {
                "value": value,
                "expires_at": expires_at
            }
        except Exception as e:
            raise CacheError(f"Error al almacenar valor en la caché: {str(e)}")
    
    def delete(self, key: str) -> None:
        """
        Elimina un valor de la caché
        
        Args:
            key: Clave del valor a eliminar
            
        Raises:
            CacheError: Si hay un error al eliminar de la caché
        """
        try:
            if key in self._cache:
                del self._cache[key]
        except Exception as e:
            raise CacheError(f"Error al eliminar valor de la caché: {str(e)}")
    
    def clear(self) -> None:
        """
        Limpia toda la caché
        
        Raises:
            CacheError: Si hay un error al limpiar la caché
        """
        try:
            self._cache.clear()
        except Exception as e:
            raise CacheError(f"Error al limpiar la caché: {str(e)}")
    
    def get_size(self) -> int:
        """
        Obtiene el tamaño actual de la caché
        
        Returns:
            Número de elementos en la caché
            
        Raises:
            CacheError: Si hay un error al obtener el tamaño
        """
        try:
            return len(self._cache)
        except Exception as e:
            raise CacheError(f"Error al obtener tamaño de la caché: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la caché
        
        Returns:
            Diccionario con estadísticas
            
        Raises:
            CacheError: Si hay un error al obtener las estadísticas
        """
        try:
            return {
                "size": len(self._cache),
                "default_ttl": self._default_ttl
            }
        except Exception as e:
            raise CacheError(f"Error al obtener estadísticas de la caché: {str(e)}") 