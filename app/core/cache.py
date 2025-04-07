from typing import Optional, Any, Dict, Union, List
import json
import hashlib
from datetime import datetime, timedelta
import redis
from app.core.config import settings
from app.core.logging import LogManager
import time
from functools import wraps, lru_cache
import asyncio
import pickle
from abc import ABC, abstractmethod
from redis.exceptions import RedisError
import logging

logger = logging.getLogger(__name__)

class CacheBackend(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass

    @abstractmethod
    async def clear(self) -> bool:
        pass

class InMemoryCache(CacheBackend):
    """Backend de caché en memoria"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor de la caché en memoria"""
        if key not in self._cache:
            return None
        
        cache_entry = self._cache[key]
        
        # Verificar si ha expirado
        if cache_entry["expires_at"] and time.time() > cache_entry["expires_at"]:
            del self._cache[key]
            return None
        
        return cache_entry["value"]
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Almacena un valor en la caché en memoria"""
        try:
            expires_at = time.time() + ttl if ttl else None
            self._cache[key] = {
                "value": value,
                "expires_at": expires_at
            }
            return True
        except Exception as e:
            LogManager.log_error("CACHE_ERROR", f"Error al almacenar en caché: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Elimina un valor de la caché en memoria"""
        try:
            if key in self._cache:
                del self._cache[key]
            return True
        except Exception as e:
            LogManager.log_error("CACHE_ERROR", f"Error al eliminar de caché: {str(e)}")
            return False
    
    async def clear(self) -> bool:
        """Limpia toda la caché en memoria"""
        try:
            self._cache.clear()
            return True
        except Exception as e:
            LogManager.log_error("CACHE_ERROR", f"Error al limpiar caché: {str(e)}")
            return False

class FileCache(CacheBackend):
    """Backend de caché en archivos"""
    
    def __init__(self, cache_dir: str = "cache"):
        import os
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_path(self, key: str) -> str:
        """Obtiene la ruta del archivo de caché para una clave"""
        import os
        # Usar hash para evitar problemas con caracteres especiales en la clave
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{key_hash}.json")
    
    async def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor de la caché en archivo"""
        import os
        cache_path = self._get_cache_path(key)
        
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, "r") as f:
                cache_entry = json.load(f)
            
            # Verificar si ha expirado
            if cache_entry["expires_at"] and time.time() > cache_entry["expires_at"]:
                os.remove(cache_path)
                return None
            
            return cache_entry["value"]
        except Exception as e:
            LogManager.log_error("CACHE_ERROR", f"Error al leer de caché: {str(e)}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Almacena un valor en la caché en archivo"""
        import os
        cache_path = self._get_cache_path(key)
        
        try:
            expires_at = time.time() + ttl if ttl else None
            cache_entry = {
                "value": value,
                "expires_at": expires_at
            }
            
            with open(cache_path, "w") as f:
                json.dump(cache_entry, f)
            
            return True
        except Exception as e:
            LogManager.log_error("CACHE_ERROR", f"Error al escribir en caché: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Elimina un valor de la caché en archivo"""
        import os
        cache_path = self._get_cache_path(key)
        
        try:
            if os.path.exists(cache_path):
                os.remove(cache_path)
            return True
        except Exception as e:
            LogManager.log_error("CACHE_ERROR", f"Error al eliminar de caché: {str(e)}")
            return False
    
    async def clear(self) -> bool:
        """Limpia toda la caché en archivo"""
        import os
        import glob
        
        try:
            for cache_file in glob.glob(os.path.join(self.cache_dir, "*.json")):
                os.remove(cache_file)
            return True
        except Exception as e:
            LogManager.log_error("CACHE_ERROR", f"Error al limpiar caché: {str(e)}")
            return False

class RedisCache(CacheBackend):
    """
    Implementación de caché distribuido usando Redis
    """
    def __init__(self):
        self._redis = None
        self._connection_pool = None
        self._serializer = pickle
        self._batch_size = 1000
        self._retry_attempts = 3
        self._retry_delay = 0.1

    @property
    def redis(self):
        if self._redis is None:
            self._connection_pool = redis.ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                ssl=settings.REDIS_SSL,
                socket_timeout=settings.REDIS_TIMEOUT,
                max_connections=settings.REDIS_MAX_CONNECTIONS
            )
            self._redis = redis.Redis(connection_pool=self._connection_pool)
        return self._redis

    async def _execute_with_retry(self, operation):
        for attempt in range(self._retry_attempts):
            try:
                return await asyncio.to_thread(operation)
            except RedisError as e:
                if attempt == self._retry_attempts - 1:
                    logger.error(f"Redis operation failed after {self._retry_attempts} attempts: {str(e)}")
                    raise
                await asyncio.sleep(self._retry_delay * (attempt + 1))

    async def get(self, key: str) -> Optional[Any]:
        try:
            value = await self._execute_with_retry(lambda: self.redis.get(key))
            if value is None:
                return None
            return self._serializer.loads(value)
        except Exception as e:
            logger.error(f"Error getting key {key}: {str(e)}")
            return None

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        try:
            serialized = self._serializer.dumps(value)
            if expire:
                return await self._execute_with_retry(
                    lambda: self.redis.setex(key, expire, serialized)
                )
            return await self._execute_with_retry(
                lambda: self.redis.set(key, serialized)
            )
        except Exception as e:
            logger.error(f"Error setting key {key}: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        try:
            return await self._execute_with_retry(lambda: self.redis.delete(key) > 0)
        except Exception as e:
            logger.error(f"Error deleting key {key}: {str(e)}")
            return False

    async def clear(self) -> bool:
        try:
            return await self._execute_with_retry(lambda: self.redis.flushdb())
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False

    async def mget(self, keys: List[str]) -> List[Optional[Any]]:
        try:
            values = await self._execute_with_retry(lambda: self.redis.mget(keys))
            return [
                self._serializer.loads(v) if v is not None else None
                for v in values
            ]
        except Exception as e:
            logger.error(f"Error getting multiple keys: {str(e)}")
            return [None] * len(keys)

    async def mset(self, mapping: Dict[str, Any], expire: Optional[int] = None) -> bool:
        try:
            pipe = self.redis.pipeline()
            for key, value in mapping.items():
                serialized = self._serializer.dumps(value)
                if expire:
                    pipe.setex(key, expire, serialized)
                else:
                    pipe.set(key, serialized)
            return await self._execute_with_retry(lambda: pipe.execute())
        except Exception as e:
            logger.error(f"Error setting multiple keys: {str(e)}")
            return False

    async def scan_iter(self, match: str = "*", count: int = 100) -> List[str]:
        try:
            cursor = 0
            keys = []
            while True:
                cursor, partial_keys = await self._execute_with_retry(
                    lambda: self.redis.scan(cursor, match=match, count=count)
                )
                keys.extend(partial_keys)
                if cursor == 0:
                    break
            return keys
        except Exception as e:
            logger.error(f"Error scanning keys: {str(e)}")
            return []

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        try:
            values = await self.mget(keys)
            return {k: v for k, v in zip(keys, values) if v is not None}
        except Exception as e:
            logger.error(f"Error getting many keys: {str(e)}")
            return {}

    async def set_many(self, mapping: Dict[str, Any], expire: Optional[int] = None) -> bool:
        try:
            return await self.mset(mapping, expire)
        except Exception as e:
            logger.error(f"Error setting many keys: {str(e)}")
            return False

    async def delete_many(self, keys: List[str]) -> int:
        try:
            return await self._execute_with_retry(lambda: self.redis.delete(*keys))
        except Exception as e:
            logger.error(f"Error deleting many keys: {str(e)}")
            return 0

# Instancia global del caché
cache = RedisCache()

class CacheManager:
    """Gestor de caché para MCP-Claude"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not CacheManager._initialized:
            # Por defecto usar caché en memoria
            self.backend = InMemoryCache()
            CacheManager._initialized = True
    
    def set_backend(self, backend: CacheBackend) -> None:
        """Establece el backend de caché a usar"""
        self.backend = backend
    
    def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor de la caché"""
        return self.backend.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Almacena un valor en la caché"""
        return self.backend.set(key, value, ttl)
    
    def delete(self, key: str) -> bool:
        """Elimina un valor de la caché"""
        return self.backend.delete(key)
    
    def clear(self) -> bool:
        """Limpia toda la caché"""
        return self.backend.clear()

def cached(ttl: Optional[int] = 3600):
    """
    Decorador para cachear resultados de funciones
    
    Args:
        ttl: Tiempo de vida en segundos (por defecto 1 hora)
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Crear clave única para la función y sus argumentos
            key_parts = [func.__name__]
            key_parts.extend([str(arg) for arg in args])
            key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
            cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # Intentar obtener de caché
            cache_manager = CacheManager()
            cached_result = cache_manager.get(cache_key)
            
            if cached_result is not None:
                LogManager.log_info(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Si no está en caché, ejecutar función
            LogManager.log_info(f"Cache miss for {func.__name__}")
            result = await func(*args, **kwargs)
            
            # Almacenar en caché
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Crear clave única para la función y sus argumentos
            key_parts = [func.__name__]
            key_parts.extend([str(arg) for arg in args])
            key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
            cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # Intentar obtener de caché
            cache_manager = CacheManager()
            cached_result = cache_manager.get(cache_key)
            
            if cached_result is not None:
                LogManager.log_info(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Si no está en caché, ejecutar función
            LogManager.log_info(f"Cache miss for {func.__name__}")
            result = func(*args, **kwargs)
            
            # Almacenar en caché
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        # Devolver el wrapper apropiado según si la función es asíncrona o no
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

class ClaudeCache:
    """Sistema de caché para Claude con soporte para respuestas de IA y resultados de búsqueda"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.default_ttl = 3600  # 1 hora por defecto
        
    def _generate_key(self, prefix: str, data: Dict[str, Any]) -> str:
        """Genera una clave única para el caché basada en los datos"""
        data_str = json.dumps(data, sort_keys=True)
        hash_obj = hashlib.sha256(data_str.encode())
        return f"claude:{prefix}:{hash_obj.hexdigest()}"
    
    def get_cached_response(self, prompt: str, model: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Obtiene una respuesta cacheada para un prompt específico"""
        cache_key = self._generate_key("response", {
            "prompt": prompt,
            "model": model,
            **kwargs
        })
        
        cached_data = self.redis_client.get(cache_key)
        if cached_data:
            LogManager.log_info("Respuesta encontrada en caché", extra={"key": cache_key})
            return json.loads(cached_data)
        return None
    
    def cache_response(self, prompt: str, response: Dict[str, Any], model: str, ttl: Optional[int] = None, **kwargs):
        """Almacena una respuesta en el caché"""
        cache_key = self._generate_key("response", {
            "prompt": prompt,
            "model": model,
            **kwargs
        })
        
        ttl = ttl or self.default_ttl
        self.redis_client.setex(
            cache_key,
            ttl,
            json.dumps(response)
        )
        LogManager.log_info("Respuesta almacenada en caché", extra={"key": cache_key, "ttl": ttl})
    
    def get_cached_search(self, query: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Obtiene resultados de búsqueda cacheados"""
        cache_key = self._generate_key("search", {
            "query": query,
            **kwargs
        })
        
        cached_data = self.redis_client.get(cache_key)
        if cached_data:
            LogManager.log_info("Resultados de búsqueda encontrados en caché", extra={"key": cache_key})
            return json.loads(cached_data)
        return None
    
    def cache_search_results(self, query: str, results: Dict[str, Any], ttl: Optional[int] = None, **kwargs):
        """Almacena resultados de búsqueda en el caché"""
        cache_key = self._generate_key("search", {
            "query": query,
            **kwargs
        })
        
        ttl = ttl or self.default_ttl
        self.redis_client.setex(
            cache_key,
            ttl,
            json.dumps(results)
        )
        LogManager.log_info("Resultados de búsqueda almacenados en caché", extra={"key": cache_key, "ttl": ttl})
    
    def invalidate_cache(self, prefix: str, data: Dict[str, Any]):
        """Invalida entradas específicas del caché"""
        cache_key = self._generate_key(prefix, data)
        self.redis_client.delete(cache_key)
        LogManager.log_info("Caché invalidado", extra={"key": cache_key})
    
    def clear_all_cache(self):
        """Limpia todo el caché"""
        keys = self.redis_client.keys("claude:*")
        if keys:
            self.redis_client.delete(*keys)
        LogManager.log_info("Caché limpiado completamente")

@lru_cache()
def get_cache() -> CacheBackend:
    return RedisCache() 