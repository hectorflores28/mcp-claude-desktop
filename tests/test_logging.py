import pytest
from pathlib import Path
import logging
from app.core.logging import LogManager

@pytest.fixture
def log_manager():
    return LogManager()

def test_log_manager_singleton():
    """Test que verifica que LogManager es un singleton"""
    manager1 = LogManager()
    manager2 = LogManager()
    assert manager1 is manager2

def test_log_directory_creation(log_manager):
    """Test que verifica la creación del directorio de logs"""
    log_dir = Path("logs")
    assert log_dir.exists()
    assert log_dir.is_dir()

def test_log_info(log_manager, caplog):
    """Test que verifica el logging de mensajes informativos"""
    test_message = "Test info message"
    LogManager.log_info(test_message)
    assert test_message in caplog.text

def test_log_error(log_manager, caplog):
    """Test que verifica el logging de errores"""
    test_message = "Test error message"
    test_error = ValueError("Test error")
    LogManager.log_error(test_message, error=test_error)
    assert test_message in caplog.text
    assert "ValueError" in caplog.text
    assert "Test error" in caplog.text

def test_log_api_request(log_manager, caplog):
    """Test que verifica el logging de solicitudes API"""
    method = "GET"
    path = "/test"
    LogManager.log_api_request(method, path)
    assert f"API Request: {method} {path}" in caplog.text

def test_log_api_response(log_manager, caplog):
    """Test que verifica el logging de respuestas API"""
    method = "GET"
    path = "/test"
    status_code = 200
    LogManager.log_api_response(method, path, status_code)
    assert f"API Response: {method} {path} - Status: {status_code}" in caplog.text

def test_log_claude_request(log_manager, caplog):
    """Test que verifica el logging de solicitudes a Claude"""
    prompt = "Test prompt"
    model = "claude-3-opus-20240229"
    LogManager.log_claude_request(prompt, model)
    assert f"Claude Request - Model: {model}" in caplog.text
    assert prompt in caplog.text

def test_log_claude_response(log_manager, caplog):
    """Test que verifica el logging de respuestas de Claude"""
    response = "Test response"
    model = "claude-3-opus-20240229"
    LogManager.log_claude_response(response, model)
    assert f"Claude Response - Model: {model}" in caplog.text
    assert response in caplog.text

def test_log_claude_streaming(log_manager, caplog):
    """Test que verifica el logging de streaming de Claude"""
    chunk = "Test chunk"
    model = "claude-3-opus-20240229"
    LogManager.log_claude_streaming(chunk, model)
    assert f"Claude Streaming - Model: {model}" in caplog.text
    assert chunk in caplog.text 