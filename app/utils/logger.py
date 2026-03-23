import logging
from logging.handlers import RotatingFileHandler
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from app.core.config import settings

class ClaudeLogger:
    """
    Sistema de logging mejorado para Claude MCP
    """
    def __init__(self, name='claude_mcp'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        
        # Configurar directorio de logs
        log_dir = settings.LOG_DIR
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Configurar archivo de log con rotación
        file_handler = RotatingFileHandler(
            f'{log_dir}/claude_mcp.log',
            maxBytes=settings.LOG_MAX_BYTES or 10*1024*1024,  # 10MB por defecto
            backupCount=settings.LOG_BACKUP_COUNT or 5
        )
        
        # Formato del log
        formatter = logging.Formatter(
            settings.LOG_FORMAT or '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Añadir handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        self.logger.info(f"Sistema de logging inicializado: {name}")
        self.logger.info(f"Directorio de logs: {log_dir}")
        self.logger.info(f"Nivel de logging: {settings.LOG_LEVEL}")
    
    def log_request(self, prompt: str, response_time: float, metadata: Optional[Dict[str, Any]] = None):
        """
        Registra una solicitud a Claude
        
        Args:
            prompt: Prompt enviado a Claude
            response_time: Tiempo de respuesta en segundos
            metadata: Metadatos adicionales
        """
        log_data = {
            "event": "request",
            "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat()
        }
        
        if metadata:
            log_data.update(metadata)
            
        self.logger.info(f"Request: {json.dumps(log_data)}")
    
    def log_error(self, error_msg: str, exception: Optional[Exception] = None, context: Optional[Dict[str, Any]] = None):
        """
        Registra un error
        
        Args:
            error_msg: Mensaje de error
            exception: Excepción (opcional)
            context: Contexto adicional (opcional)
        """
        log_data = {
            "event": "error",
            "message": error_msg,
            "timestamp": datetime.now().isoformat()
        }
        
        if context:
            log_data.update(context)
            
        if exception:
            self.logger.error(f"Error: {json.dumps(log_data)}", exc_info=exception)
        else:
            self.logger.error(f"Error: {json.dumps(log_data)}")
    
    def log_info(self, message: str, data: Optional[Dict[str, Any]] = None):
        """
        Registra información
        
        Args:
            message: Mensaje informativo
            data: Datos adicionales (opcional)
        """
        log_data = {
            "event": "info",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        if data:
            log_data.update(data)
            
        self.logger.info(f"Info: {json.dumps(log_data)}")
    
    def log_warning(self, message: str, data: Optional[Dict[str, Any]] = None):
        """
        Registra una advertencia
        
        Args:
            message: Mensaje de advertencia
            data: Datos adicionales (opcional)
        """
        log_data = {
            "event": "warning",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        if data:
            log_data.update(data)
            
        self.logger.warning(f"Warning: {json.dumps(log_data)}")
    
    def log_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Registra una métrica
        
        Args:
            name: Nombre de la métrica
            value: Valor de la métrica
            tags: Etiquetas adicionales (opcional)
        """
        log_data = {
            "event": "metric",
            "name": name,
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        
        if tags:
            log_data["tags"] = tags
            
        self.logger.info(f"Metric: {json.dumps(log_data)}")
    
    def log_api_call(self, endpoint: str, method: str, status_code: int, response_time: float, 
                    request_data: Optional[Dict[str, Any]] = None, response_data: Optional[Dict[str, Any]] = None):
        """
        Registra una llamada a la API
        
        Args:
            endpoint: Endpoint de la API
            method: Método HTTP
            status_code: Código de estado HTTP
            response_time: Tiempo de respuesta en segundos
            request_data: Datos de la solicitud (opcional)
            response_data: Datos de la respuesta (opcional)
        """
        log_data = {
            "event": "api_call",
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat()
        }
        
        if request_data:
            log_data["request"] = request_data
            
        if response_data:
            log_data["response"] = response_data
            
        self.logger.info(f"API Call: {json.dumps(log_data)}") 