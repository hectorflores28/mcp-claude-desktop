import os
import json
import pytest
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from app.core.logging.claude_logger import ClaudeLogger

class TestClaudeLogger:
    """Pruebas unitarias para el sistema de logs de Claude"""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Fixture para crear un directorio temporal para los logs"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def claude_logger(self, temp_log_dir):
        """Fixture para inicializar el logger de Claude"""
        return ClaudeLogger(temp_log_dir)
    
    def test_setup_log_dirs(self, temp_log_dir):
        """Prueba la creación de directorios de logs"""
        logger = ClaudeLogger(temp_log_dir)
        
        # Verificar que se crearon los directorios
        assert os.path.exists(os.path.join(temp_log_dir, "app"))
        assert os.path.exists(os.path.join(temp_log_dir, "access"))
        assert os.path.exists(os.path.join(temp_log_dir, "error"))
    
    def test_setup_loggers(self, claude_logger):
        """Prueba la configuración de los loggers"""
        # Verificar que se crearon los loggers
        assert claude_logger.app_logger is not None
        assert claude_logger.access_logger is not None
        assert claude_logger.error_logger is not None
        
        # Verificar que los loggers tienen el nivel correcto
        assert claude_logger.app_logger.level == 20  # INFO
        assert claude_logger.access_logger.level == 20  # INFO
        assert claude_logger.error_logger.level == 20  # INFO
    
    @patch('logging.Logger.info')
    def test_log_request(self, mock_info, claude_logger):
        """Prueba el registro de solicitudes"""
        # Llamar al método
        claude_logger.log_request("Test prompt", "claude-3-opus", 100, 0.5)
        
        # Verificar que se llamó al logger
        mock_info.assert_called_once()
        
        # Verificar el contenido del log
        log_entry = json.loads(mock_info.call_args[0][0])
        assert log_entry["type"] == "request"
        assert log_entry["model"] == "claude-3-opus"
        assert log_entry["prompt_length"] == 11
        assert log_entry["tokens"] == 100
        assert log_entry["response_time"] == 0.5
    
    @patch('logging.Logger.info')
    def test_log_response(self, mock_info, claude_logger):
        """Prueba el registro de respuestas"""
        # Llamar al método
        claude_logger.log_response("Test prompt", "claude-3-opus", "Test response", 150, 0.7)
        
        # Verificar que se llamó al logger
        mock_info.assert_called_once()
        
        # Verificar el contenido del log
        log_entry = json.loads(mock_info.call_args[0][0])
        assert log_entry["type"] == "response"
        assert log_entry["model"] == "claude-3-opus"
        assert log_entry["prompt_length"] == 11
        assert log_entry["response_length"] == 13
        assert log_entry["tokens"] == 150
        assert log_entry["response_time"] == 0.7
    
    @patch('logging.Logger.error')
    def test_log_error(self, mock_error, claude_logger):
        """Prueba el registro de errores"""
        # Llamar al método
        claude_logger.log_error("API_ERROR", "Error de API", {"status_code": 500})
        
        # Verificar que se llamó al logger
        mock_error.assert_called_once()
        
        # Verificar el contenido del log
        log_entry = json.loads(mock_error.call_args[0][0])
        assert log_entry["type"] == "error"
        assert log_entry["error_type"] == "API_ERROR"
        assert log_entry["error_message"] == "Error de API"
        assert log_entry["context"]["status_code"] == 500
    
    @patch('logging.Logger.info')
    def test_log_app_info(self, mock_info, claude_logger):
        """Prueba el registro de mensajes de la aplicación (info)"""
        # Llamar al método
        claude_logger.log_app("info", "Test message", {"key": "value"})
        
        # Verificar que se llamó al logger
        mock_info.assert_called_once()
        
        # Verificar el contenido del log
        log_entry = json.loads(mock_info.call_args[0][0])
        assert log_entry["level"] == "info"
        assert log_entry["message"] == "Test message"
        assert log_entry["context"]["key"] == "value"
    
    @patch('logging.Logger.warning')
    def test_log_app_warning(self, mock_warning, claude_logger):
        """Prueba el registro de mensajes de la aplicación (warning)"""
        # Llamar al método
        claude_logger.log_app("warning", "Test warning", {"key": "value"})
        
        # Verificar que se llamó al logger
        mock_warning.assert_called_once()
        
        # Verificar el contenido del log
        log_entry = json.loads(mock_warning.call_args[0][0])
        assert log_entry["level"] == "warning"
        assert log_entry["message"] == "Test warning"
        assert log_entry["context"]["key"] == "value"
    
    @patch('logging.Logger.error')
    def test_log_app_error(self, mock_error, claude_logger):
        """Prueba el registro de mensajes de la aplicación (error)"""
        # Llamar al método
        claude_logger.log_app("error", "Test error", {"key": "value"})
        
        # Verificar que se llamó al logger
        mock_error.assert_called_once()
        
        # Verificar el contenido del log
        log_entry = json.loads(mock_error.call_args[0][0])
        assert log_entry["level"] == "error"
        assert log_entry["message"] == "Test error"
        assert log_entry["context"]["key"] == "value" 