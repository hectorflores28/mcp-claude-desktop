from pythonjsonlogger import jsonlogger
import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from app.core.config import settings
from app.core.markdown_logger import MarkdownLogger
import json
import time
from pathlib import Path
import asyncio
from app.core.cache import get_cache

# Asegurar que el directorio de logs existe
log_dir = Path(settings.LOG_DIR)
log_dir.mkdir(exist_ok=True, parents=True)

# Obtener el nivel de logging
try:
    log_level = getattr(logging, settings.LOG_LEVEL.upper())
except AttributeError:
    log_level = logging.INFO
    print(f"Advertencia: Nivel de logging '{settings.LOG_LEVEL}' no válido. Usando INFO.")

# Configurar logging básico
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.handlers.RotatingFileHandler(
            log_dir / "app.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("mcp-claude")

class ClaudeLogFormatter(logging.Formatter):
    """Formateador personalizado para logs de Claude en formato JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
            
        return json.dumps(log_data)

class LogManager:
    """Gestor de logs con soporte para procesamiento en lote"""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._cache = get_cache()
            self._batch_size = 100
            self._flush_interval = 60  # 1 minuto
            self._last_flush = time.time()
            
            # Buffers para logs
            self._info_buffer: List[Dict] = []
            self._error_buffer: List[Dict] = []
            self._request_buffer: List[Dict] = []
            
            # Configurar handlers
            self._setup_handlers()
            
            self._initialized = True
    
    def _setup_handlers(self):
        """Configura los handlers de logging"""
        # Handler para logs JSON
        json_handler = logging.handlers.RotatingFileHandler(
            log_dir / "claude.json",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        json_handler.setFormatter(ClaudeLogFormatter())
        
        # Handler para logs de requests
        request_handler = logging.handlers.RotatingFileHandler(
            log_dir / "requests.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        request_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(method)s - %(url)s - %(status_code)s - %(process_time).2fs'
        ))
        
        # Añadir handlers al logger
        logger.addHandler(json_handler)
        logger.addHandler(request_handler)
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Obtiene un logger con el nombre especificado
        
        Args:
            name: Nombre del logger
            
        Returns:
            Logger configurado
        """
        return logging.getLogger(name)
    
    async def log_info(self, message: str, extra: Optional[Dict] = None) -> None:
        """
        Registra un mensaje de información
        
        Args:
            message: Mensaje a registrar
            extra: Datos adicionales
        """
        try:
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": message,
                "extra": extra or {}
            }
            
            self._info_buffer.append(log_data)
            await self._flush_if_needed()
            
            logger.info(message, extra=extra or {})
        except Exception as e:
            print(f"Error al registrar log de información: {str(e)}")
    
    async def log_error(self, message: str, error: Optional[Exception] = None, extra: Optional[Dict] = None) -> None:
        """
        Registra un mensaje de error
        
        Args:
            message: Mensaje a registrar
            error: Excepción asociada
            extra: Datos adicionales
        """
        try:
            error_data = {
                "type": error.__class__.__name__ if error else None,
                "message": str(error) if error else None,
                "traceback": getattr(error, "__traceback__", None)
            }
            
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "level": "ERROR",
                "message": message,
                "error": error_data,
                "extra": extra or {}
            }
            
            self._error_buffer.append(log_data)
            await self._flush_if_needed()
            
            logger.error(message, exc_info=error, extra=extra or {})
        except Exception as e:
            print(f"Error al registrar log de error: {str(e)}")
    
    async def log_request(self, method: str, url: str, status_code: int, process_time: float) -> None:
        """
        Registra una solicitud HTTP
        
        Args:
            method: Método HTTP
            url: URL de la solicitud
            status_code: Código de estado
            process_time: Tiempo de procesamiento
        """
        try:
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "method": method,
                "url": url,
                "status_code": status_code,
                "process_time": process_time
            }
            
            self._request_buffer.append(log_data)
            await self._flush_if_needed()
            
            logger.info(
                f"{method} {url} - {status_code} - {process_time:.2f}s",
                extra={"method": method, "url": url, "status_code": status_code, "process_time": process_time}
            )
        except Exception as e:
            print(f"Error al registrar log de solicitud: {str(e)}")
    
    async def _flush_if_needed(self) -> None:
        """
        Flush los buffers si es necesario
        """
        current_time = time.time()
        if (current_time - self._last_flush >= self._flush_interval or
            len(self._info_buffer) >= self._batch_size or
            len(self._error_buffer) >= self._batch_size or
            len(self._request_buffer) >= self._batch_size):
            await self._flush()
    
    async def _flush(self) -> None:
        """
        Flush los buffers a Redis
        """
        async with self._lock:
            try:
                # Preparar datos para info logs
                if self._info_buffer:
                    await self._cache.set_many({
                        f"logs:info:{i}": data
                        for i, data in enumerate(self._info_buffer)
                    }, ttl=86400)  # 24 horas
                    self._info_buffer.clear()
                
                # Preparar datos para error logs
                if self._error_buffer:
                    await self._cache.set_many({
                        f"logs:error:{i}": data
                        for i, data in enumerate(self._error_buffer)
                    }, ttl=86400)  # 24 horas
                    self._error_buffer.clear()
                
                # Preparar datos para request logs
                if self._request_buffer:
                    await self._cache.set_many({
                        f"logs:request:{i}": data
                        for i, data in enumerate(self._request_buffer)
                    }, ttl=86400)  # 24 horas
                    self._request_buffer.clear()
                
                self._last_flush = time.time()
            except Exception as e:
                print(f"Error al almacenar logs: {str(e)}")
    
    async def get_info_logs(self, limit: int = 100) -> List[Dict]:
        """
        Obtiene logs de información
        
        Args:
            limit: Límite de logs a obtener
            
        Returns:
            Lista de logs
        """
        try:
            keys = [f"logs:info:{i}" for i in range(limit)]
            values = await self._cache.get_many(keys)
            
            logs = []
            for value in values.values():
                if value:
                    logs.append(value)
            
            return sorted(
                logs,
                key=lambda x: x["timestamp"],
                reverse=True
            )
        except Exception as e:
            print(f"Error al obtener logs de información: {str(e)}")
            return []
    
    async def get_error_logs(self, limit: int = 100) -> List[Dict]:
        """
        Obtiene logs de error
        
        Args:
            limit: Límite de logs a obtener
            
        Returns:
            Lista de logs
        """
        try:
            keys = [f"logs:error:{i}" for i in range(limit)]
            values = await self._cache.get_many(keys)
            
            logs = []
            for value in values.values():
                if value:
                    logs.append(value)
            
            return sorted(
                logs,
                key=lambda x: x["timestamp"],
                reverse=True
            )
        except Exception as e:
            print(f"Error al obtener logs de error: {str(e)}")
            return []
    
    async def get_request_logs(self, limit: int = 100) -> List[Dict]:
        """
        Obtiene logs de solicitudes
        
        Args:
            limit: Límite de logs a obtener
            
        Returns:
            Lista de logs
        """
        try:
            keys = [f"logs:request:{i}" for i in range(limit)]
            values = await self._cache.get_many(keys)
            
            logs = []
            for value in values.values():
                if value:
                    logs.append(value)
            
            return sorted(
                logs,
                key=lambda x: x["timestamp"],
                reverse=True
            )
        except Exception as e:
            print(f"Error al obtener logs de solicitudes: {str(e)}")
            return []

# Instancia global del gestor de logs
log_manager = LogManager() 