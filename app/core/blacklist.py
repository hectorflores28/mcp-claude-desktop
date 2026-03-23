from typing import Optional, Set, List, Dict, Any
import time
import asyncio
from functools import lru_cache
import logging
from datetime import datetime, timedelta
import backoff

from app.core.cache import get_cache

logger = logging.getLogger(__name__)

class TokenBlacklist:
    """
    Sistema de lista negra de tokens con soporte para limpieza automática y operaciones en lote
    """
    def __init__(self):
        self._cache = get_cache()
        self._prefix = "blacklist:"
        self._batch_size = 1000
        self._cleanup_interval = 3600  # 1 hora
        self._last_cleanup = time.time()
        self._cleanup_lock = asyncio.Lock()

    def _get_key(self, token: str) -> str:
        """Genera la clave para un token en la blacklist"""
        return f"{self._prefix}{token}"

    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        max_time=5
    )
    async def _cleanup_expired(self):
        """
        Limpia tokens expirados de forma eficiente usando procesamiento en lote
        """
        current_time = time.time()
        if current_time - self._last_cleanup < self._cleanup_interval:
            return

        async with self._cleanup_lock:
            try:
                # Obtener todas las claves de blacklist
                keys = await self._cache.scan_iter(match=f"{self._prefix}*")
                
                # Procesar en lotes
                for i in range(0, len(keys), self._batch_size):
                    batch = keys[i:i + self._batch_size]
                    # Verificar TTL de cada clave en el lote
                    for key in batch:
                        ttl = await self._cache.get_ttl(key)
                        if ttl is None or ttl <= 0:
                            await self._cache.delete(key)
                
                self._last_cleanup = current_time
                logger.info(f"Limpieza de blacklist completada: {len(keys)} tokens procesados")
            except Exception as e:
                logger.error(f"Error durante la limpieza de blacklist: {str(e)}")
                raise

    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        max_time=5
    )
    async def add_token(self, token: str, expires_in: int = 3600) -> bool:
        """
        Añade un token a la blacklist
        
        Args:
            token: Token a añadir
            expires_in: Tiempo de expiración en segundos
            
        Returns:
            True si se añadió correctamente
        """
        try:
            key = self._get_key(token)
            await self._cache.set(key, True, ttl=expires_in)
            return True
        except Exception as e:
            logger.error(f"Error al añadir token a blacklist: {str(e)}")
            return False

    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        max_time=5
    )
    async def is_blacklisted(self, token: str) -> bool:
        """
        Verifica si un token está en la blacklist
        
        Args:
            token: Token a verificar
            
        Returns:
            True si el token está en la blacklist
        """
        try:
            key = self._get_key(token)
            return await self._cache.exists(key)
        except Exception as e:
            logger.error(f"Error al verificar token en blacklist: {str(e)}")
            return False

    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        max_time=5
    )
    async def remove_token(self, token: str) -> bool:
        """
        Elimina un token de la blacklist
        
        Args:
            token: Token a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            key = self._get_key(token)
            return await self._cache.delete(key)
        except Exception as e:
            logger.error(f"Error al eliminar token de blacklist: {str(e)}")
            return False

    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        max_time=5
    )
    async def add_tokens_batch(self, tokens: List[str], expires_in: int = 3600) -> Dict[str, bool]:
        """
        Añade múltiples tokens a la blacklist en un solo lote
        
        Args:
            tokens: Lista de tokens a añadir
            expires_in: Tiempo de expiración en segundos
            
        Returns:
            Diccionario con el resultado de cada token
        """
        try:
            if not tokens:
                return {}
                
            # Preparar mapeo de tokens
            mapping = {self._get_key(token): True for token in tokens}
            
            # Almacenar en lote
            success = await self._cache.set_many(mapping, ttl=expires_in)
            
            # Preparar resultado
            result = {token: success for token in tokens}
            return result
        except Exception as e:
            logger.error(f"Error al añadir tokens en lote a blacklist: {str(e)}")
            return {token: False for token in tokens}

    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        max_time=5
    )
    async def check_tokens_batch(self, tokens: List[str]) -> Dict[str, bool]:
        """
        Verifica múltiples tokens en la blacklist en un solo lote
        
        Args:
            tokens: Lista de tokens a verificar
            
        Returns:
            Diccionario con el estado de cada token
        """
        try:
            if not tokens:
                return {}
                
            # Obtener claves
            keys = [self._get_key(token) for token in tokens]
            
            # Verificar existencia en lote
            exists_map = await self._cache.get_many(keys)
            
            # Preparar resultado
            result = {token: self._get_key(token) in exists_map for token in tokens}
            return result
        except Exception as e:
            logger.error(f"Error al verificar tokens en lote en blacklist: {str(e)}")
            return {token: False for token in tokens}

    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        max_time=5
    )
    async def remove_tokens_batch(self, tokens: List[str]) -> Dict[str, bool]:
        """
        Elimina múltiples tokens de la blacklist en un solo lote
        
        Args:
            tokens: Lista de tokens a eliminar
            
        Returns:
            Diccionario con el resultado de cada token
        """
        try:
            if not tokens:
                return {}
                
            # Obtener claves
            keys = [self._get_key(token) for token in tokens]
            
            # Eliminar en lote
            success = await self._cache.delete_many(keys)
            
            # Preparar resultado
            result = {token: success for token in tokens}
            return result
        except Exception as e:
            logger.error(f"Error al eliminar tokens en lote de blacklist: {str(e)}")
            return {token: False for token in tokens}

# Instancia global de blacklist con decorador lru_cache
@lru_cache()
def get_blacklist() -> TokenBlacklist:
    """
    Obtiene una instancia de la blacklist.
    
    Returns:
        Instancia de TokenBlacklist
    """
    return TokenBlacklist()

# Instancia global de blacklist
blacklist = get_blacklist() 