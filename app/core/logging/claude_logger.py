import json
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

class ClaudeLogger:
    """Sistema de logs estandarizado para MCP-Claude"""
    
    def __init__(self, log_dir):
        """
        Inicializa el sistema de logs
        
        Args:
            log_dir (str): Directorio base para los logs
        """
        self.log_dir = log_dir
        self.setup_log_dirs()
        self.setup_loggers()
    
    def setup_log_dirs(self):
        """Crea los directorios necesarios para los logs"""
        os.makedirs(os.path.join(self.log_dir, "app"), exist_ok=True)
        os.makedirs(os.path.join(self.log_dir, "access"), exist_ok=True)
        os.makedirs(os.path.join(self.log_dir, "error"), exist_ok=True)
    
    def setup_loggers(self):
        """Configura los loggers específicos para Claude"""
        # Logger para la aplicación
        self.app_logger = self._setup_logger(
            "claude_app", 
            os.path.join(self.log_dir, "app", "app.log"),
            max_bytes=10*1024*1024,  # 10MB
            backup_count=5
        )
        
        # Logger para accesos
        self.access_logger = self._setup_logger(
            "claude_access", 
            os.path.join(self.log_dir, "access", "access.log"),
            max_bytes=5*1024*1024,  # 5MB
            backup_count=3
        )
        
        # Logger para errores
        self.error_logger = self._setup_logger(
            "claude_error", 
            os.path.join(self.log_dir, "error", "error.log"),
            max_bytes=5*1024*1024,  # 5MB
            backup_count=3
        )
    
    def _setup_logger(self, name, log_file, max_bytes=10*1024*1024, backup_count=5):
        """
        Configura un logger con rotación de archivos
        
        Args:
            name (str): Nombre del logger
            log_file (str): Ruta al archivo de log
            max_bytes (int): Tamaño máximo del archivo antes de rotar
            backup_count (int): Número de archivos de respaldo a mantener
            
        Returns:
            logging.Logger: Logger configurado
        """
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        
        # Formato JSON para los logs
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Handler con rotación de archivos
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=max_bytes, 
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def log_request(self, prompt, model, tokens, response_time=None):
        """
        Registra una solicitud a la API de Claude
        
        Args:
            prompt (str): Prompt enviado a Claude
            model (str): Modelo utilizado
            tokens (int): Número de tokens utilizados
            response_time (float, optional): Tiempo de respuesta en segundos
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "request",
            "model": model,
            "prompt_length": len(prompt),
            "tokens": tokens,
            "response_time": response_time
        }
        self.access_logger.info(json.dumps(log_entry))
    
    def log_response(self, prompt, model, response, tokens, response_time=None):
        """
        Registra una respuesta de la API de Claude
        
        Args:
            prompt (str): Prompt enviado a Claude
            model (str): Modelo utilizado
            response (str): Respuesta recibida
            tokens (int): Número de tokens utilizados
            response_time (float, optional): Tiempo de respuesta en segundos
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "response",
            "model": model,
            "prompt_length": len(prompt),
            "response_length": len(response),
            "tokens": tokens,
            "response_time": response_time
        }
        self.access_logger.info(json.dumps(log_entry))
    
    def log_error(self, error_type, error_message, context=None):
        """
        Registra un error
        
        Args:
            error_type (str): Tipo de error
            error_message (str): Mensaje de error
            context (dict, optional): Contexto adicional del error
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "error",
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {}
        }
        self.error_logger.error(json.dumps(log_entry))
    
    def log_app(self, level, message, context=None):
        """
        Registra un mensaje de la aplicación
        
        Args:
            level (str): Nivel de log (info, warning, error)
            message (str): Mensaje a registrar
            context (dict, optional): Contexto adicional
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "context": context or {}
        }
        
        if level == "info":
            self.app_logger.info(json.dumps(log_entry))
        elif level == "warning":
            self.app_logger.warning(json.dumps(log_entry))
        elif level == "error":
            self.app_logger.error(json.dumps(log_entry)) 