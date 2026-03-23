"""
Sistema de caché distribuido con Redis.

Este módulo proporciona una interfaz para el manejo de caché distribuido
utilizando Redis como backend.
"""

import json
import logging
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import redis
from redis.exceptions import RedisError
from backoff import on_exception, expo
from app.config.settings import settings
from redis.connection import ConnectionPool
from functools import lru_cache

logger = logging.getLogger(__name__)

class CacheError(Exception):
    """Excepción base para errores de caché."""
    pass

class CacheConnectionError(CacheError):
    """Error de conexión con Redis."""
    pass

class CacheOperationError(CacheError):
    """Error en operaciones de caché."""
    pass

class Cache:
    """Clase para manejo de caché con Redis."""
    
    def __init__(self):
        """Inicializa el cliente de Redis con configuración optimizada."""
        try:
            # Configurar pool de conexiones
            connection_kwargs = {
                'host': settings.REDIS_HOST,
                'port': settings.REDIS_PORT,
                'password': settings.REDIS_PASSWORD,
                'db': settings.REDIS_DB,
                'socket_timeout': settings.REDIS_TIMEOUT,
                'socket_connect_timeout': settings.REDIS_TIMEOUT,
                'max_connections': settings.REDIS_MAX_CONNECTIONS,
                'retry_on_timeout': True,
                'decode_responses': True
            }
            
            if settings.REDIS_SSL:
                connection_kwargs['ssl'] = True
            
            self.pool = ConnectionPool(**connection_kwargs)
            
            self.redis = redis.Redis(connection_pool=self.pool)
            self.prefix = settings.CACHE_PREFIX
            self.default_ttl = settings.CACHE_TTL
            self._test_connection()
        except RedisError as e:
            logger.error(f"Error al inicializar Redis: {str(e)}")
            raise CacheConnectionError(f"Error de conexión con Redis: {str(e)}")
    
    def _test_connection(self) -> None:
        """Prueba la conexión con Redis."""
        try:
            self.redis.ping()
        except RedisError as e:
            logger.error(f"Error al probar conexión con Redis: {str(e)}")
            raise CacheConnectionError(f"Error de conexión con Redis: {str(e)}")
    
    @on_exception(expo, RedisError, max_tries=3, max_time=5)
    def get(self, key: str) -> Optional[Any]:
        """
        Obtiene un valor del caché.
        
        Args:
            key: Clave a buscar
            
        Returns:
            Valor almacenado o None si no existe
            
        Raises:
            CacheOperationError: Si hay un error en la operación
        """
        try:
            full_key = f"{self.prefix}{key}"
            value = self.redis.get(full_key)
            if value:
                return json.loads(value)
            return None
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Error al obtener valor de caché: {str(e)}")
            raise CacheOperationError(f"Error al obtener valor de caché: {str(e)}")
    
    @on_exception(expo, RedisError, max_tries=3, max_time=5)
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Almacena un valor en el caché.
        
        Args:
            key: Clave para almacenar
            value: Valor a almacenar
            ttl: Tiempo de vida en segundos (opcional)
            
        Returns:
            True si se almacenó correctamente
            
        Raises:
            CacheOperationError: Si hay un error en la operación
        """
        try:
            full_key = f"{self.prefix}{key}"
            serialized = json.dumps(value)
            return self.redis.set(
                full_key,
                serialized,
                ex=ttl or self.default_ttl
            )
        except (RedisError, TypeError) as e:
            logger.error(f"Error al almacenar en caché: {str(e)}")
            raise CacheOperationError(f"Error al almacenar en caché: {str(e)}")
    
    @on_exception(expo, RedisError, max_tries=3, max_time=5)
    def delete(self, key: str) -> bool:
        """
        Elimina un valor del caché.
        
        Args:
            key: Clave a eliminar
            
        Returns:
            True si se eliminó correctamente
            
        Raises:
            CacheOperationError: Si hay un error en la operación
        """
        try:
            full_key = f"{self.prefix}{key}"
            return bool(self.redis.delete(full_key))
        except RedisError as e:
            logger.error(f"Error al eliminar de caché: {str(e)}")
            raise CacheOperationError(f"Error al eliminar de caché: {str(e)}")
    
    @on_exception(expo, RedisError, max_tries=3, max_time=5)
    def exists(self, key: str) -> bool:
        """
        Verifica si existe una clave en el caché.
        
        Args:
            key: Clave a verificar
            
        Returns:
            True si existe la clave
            
        Raises:
            CacheOperationError: Si hay un error en la operación
        """
        try:
            full_key = f"{self.prefix}{key}"
            return bool(self.redis.exists(full_key))
        except RedisError as e:
            logger.error(f"Error al verificar existencia en caché: {str(e)}")
            raise CacheOperationError(f"Error al verificar existencia en caché: {str(e)}")
    
    @on_exception(expo, RedisError, max_tries=3, max_time=5)
    def clear(self) -> bool:
        """
        Limpia todo el caché.
        
        Returns:
            True si se limpió correctamente
            
        Raises:
            CacheOperationError: Si hay un error en la operación
        """
        try:
            pattern = f"{self.prefix}*"
            keys = self.redis.keys(pattern)
            if keys:
                return bool(self.redis.delete(*keys))
            return True
        except RedisError as e:
            logger.error(f"Error al limpiar caché: {str(e)}")
            raise CacheOperationError(f"Error al limpiar caché: {str(e)}")
    
    @on_exception(expo, RedisError, max_tries=3, max_time=5)
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Obtiene múltiples valores del caché.
        
        Args:
            keys: Lista de claves a obtener
            
        Returns:
            Diccionario con los valores encontrados
            
        Raises:
            CacheOperationError: Si hay un error en la operación
        """
        try:
            if not keys:
                return {}
                
            full_keys = [f"{self.prefix}{key}" for key in keys]
            values = self.redis.mget(full_keys)
            
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        continue
                        
            return result
        except RedisError as e:
            logger.error(f"Error al obtener múltiples valores de caché: {str(e)}")
            raise CacheOperationError(f"Error al obtener múltiples valores de caché: {str(e)}")
    
    @on_exception(expo, RedisError, max_tries=3, max_time=5)
    def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Almacena múltiples valores en el caché.
        
        Args:
            mapping: Diccionario con claves y valores
            ttl: Tiempo de vida en segundos (opcional)
            
        Returns:
            True si se almacenaron correctamente
            
        Raises:
            CacheOperationError: Si hay un error en la operación
        """
        try:
            if not mapping:
                return True
                
            pipe = self.redis.pipeline()
            for key, value in mapping.items():
                full_key = f"{self.prefix}{key}"
                serialized = json.dumps(value)
                pipe.set(full_key, serialized, ex=ttl or self.default_ttl)
                
            results = pipe.execute()
            return all(results)
        except (RedisError, TypeError) as e:
            logger.error(f"Error al almacenar múltiples valores en caché: {str(e)}")
            raise CacheOperationError(f"Error al almacenar múltiples valores en caché: {str(e)}")
    
    @on_exception(expo, RedisError, max_tries=3, max_time=5)
    def delete_many(self, keys: List[str]) -> bool:
        """
        Elimina múltiples valores del caché.
        
        Args:
            keys: Lista de claves a eliminar
            
        Returns:
            True si se eliminaron correctamente
            
        Raises:
            CacheOperationError: Si hay un error en la operación
        """
        try:
            if not keys:
                return True
                
            full_keys = [f"{self.prefix}{key}" for key in keys]
            return bool(self.redis.delete(*full_keys))
        except RedisError as e:
            logger.error(f"Error al eliminar múltiples valores de caché: {str(e)}")
            raise CacheOperationError(f"Error al eliminar múltiples valores de caché: {str(e)}")
    
    @on_exception(expo, RedisError, max_tries=3, max_time=5)
    def increment(self, key: str, amount: int = 1) -> int:
        """
        Incrementa un contador en el caché.
        
        Args:
            key: Clave del contador
            amount: Cantidad a incrementar
            
        Returns:
            Nuevo valor del contador
            
        Raises:
            CacheOperationError: Si hay un error en la operación
        """
        try:
            full_key = f"{self.prefix}{key}"
            return self.redis.incrby(full_key, amount)
        except RedisError as e:
            logger.error(f"Error al incrementar contador en caché: {str(e)}")
            raise CacheOperationError(f"Error al incrementar contador en caché: {str(e)}")
    
    @on_exception(expo, RedisError, max_tries=3, max_time=5)
    def decrement(self, key: str, amount: int = 1) -> int:
        """
        Decrementa un contador en el caché.
        
        Args:
            key: Clave del contador
            amount: Cantidad a decrementar
            
        Returns:
            Nuevo valor del contador
            
        Raises:
            CacheOperationError: Si hay un error en la operación
        """
        try:
            full_key = f"{self.prefix}{key}"
            return self.redis.decrby(full_key, amount)
        except RedisError as e:
            logger.error(f"Error al decrementar contador en caché: {str(e)}")
            raise CacheOperationError(f"Error al decrementar contador en caché: {str(e)}")
    
    @on_exception(expo, RedisError, max_tries=3, max_time=5)
    def get_ttl(self, key: str) -> Optional[int]:
        """
        Obtiene el tiempo restante de vida de una clave.
        
        Args:
            key: Clave a verificar
            
        Returns:
            Tiempo restante en segundos o None si no existe
            
        Raises:
            CacheOperationError: Si hay un error en la operación
        """
        try:
            full_key = f"{self.prefix}{key}"
            ttl = self.redis.ttl(full_key)
            return ttl if ttl > 0 else None
        except RedisError as e:
            logger.error(f"Error al obtener TTL de caché: {str(e)}")
            raise CacheOperationError(f"Error al obtener TTL de caché: {str(e)}")
    
    @on_exception(expo, RedisError, max_tries=3, max_time=5)
    def touch(self, key: str, ttl: Optional[int] = None) -> bool:
        """
        Actualiza el tiempo de vida de una clave.
        
        Args:
            key: Clave a actualizar
            ttl: Nuevo tiempo de vida en segundos (opcional)
            
        Returns:
            True si se actualizó correctamente
            
        Raises:
            CacheOperationError: Si hay un error en la operación
        """
        try:
            full_key = f"{self.prefix}{key}"
            if ttl is not None:
                return bool(self.redis.expire(full_key, ttl))
            return bool(self.redis.expire(full_key, self.default_ttl))
        except RedisError as e:
            logger.error(f"Error al actualizar TTL en caché: {str(e)}")
            raise CacheOperationError(f"Error al actualizar TTL en caché: {str(e)}")

# Instancia global de caché con decorador lru_cache para evitar múltiples instancias
@lru_cache()
def get_cache() -> Cache:
    """
    Obtiene una instancia del caché.
    
    Returns:
        Instancia de Cache
    """
    return Cache()

# Instancia global de caché
cache = get_cache() 