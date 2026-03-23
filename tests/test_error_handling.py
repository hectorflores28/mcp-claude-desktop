import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.core.exceptions import (
    MCPClaudeError,
    ClaudeAPIError,
    ClaudeRateLimitError,
    ClaudeAuthenticationError,
    ClaudeValidationError,
    ClaudeStreamingError
)

app = FastAPI()
client = TestClient(app)

def test_claude_api_error():
    """Test que verifica el manejo de errores de API de Claude"""
    error = ClaudeAPIError("Test API error", status_code=500)
    assert error.status_code == 500
    assert error.error_code == "CLAUDE_API_ERROR"
    assert error.message == "Test API error"

def test_claude_rate_limit_error():
    """Test que verifica el manejo de errores de límite de tasa"""
    error = ClaudeRateLimitError()
    assert error.status_code == 429
    assert error.error_code == "CLAUDE_API_ERROR"
    assert "Rate limit exceeded" in error.message

def test_claude_authentication_error():
    """Test que verifica el manejo de errores de autenticación"""
    error = ClaudeAuthenticationError()
    assert error.status_code == 401
    assert error.error_code == "CLAUDE_API_ERROR"
    assert "Authentication failed" in error.message

def test_claude_validation_error():
    """Test que verifica el manejo de errores de validación"""
    error = ClaudeValidationError("Invalid input")
    assert error.status_code == 400
    assert error.error_code == "VALIDATION_ERROR"
    assert error.message == "Invalid input"

def test_claude_streaming_error():
    """Test que verifica el manejo de errores de streaming"""
    error = ClaudeStreamingError("Streaming failed")
    assert error.status_code == 500
    assert error.error_code == "STREAMING_ERROR"
    assert error.message == "Streaming failed"

def test_error_with_details():
    """Test que verifica el manejo de errores con detalles adicionales"""
    details = {"field": "test", "reason": "invalid"}
    error = ClaudeValidationError("Invalid input", details=details)
    assert error.details == details
    assert error.status_code == 400

def test_error_inheritance():
    """Test que verifica la jerarquía de herencia de errores"""
    error = ClaudeRateLimitError()
    assert isinstance(error, ClaudeAPIError)
    assert isinstance(error, MCPClaudeError)
    assert not isinstance(error, ClaudeValidationError) 