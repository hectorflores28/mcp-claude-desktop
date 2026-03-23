from typing import Optional, Dict, Any
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import traceback
from app.core.logging import LogManager

class MCPClaudeError(Exception):
    """Excepción base para errores de MCP-Claude"""
    def __init__(
        self, 
        message: str, 
        error_code: str, 
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ClaudeAPIError(MCPClaudeError):
    """Error en la API de Claude"""
    def __init__(
        self, 
        message: str, 
        error_code: str = "CLAUDE_API_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, status_code, details)

class ClaudeRateLimitError(ClaudeAPIError):
    """Error de límite de tasa de Claude"""
    def __init__(
        self, 
        message: str = "Rate limit exceeded for Claude API",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message, 
            "CLAUDE_RATE_LIMIT_ERROR", 
            429, 
            details
        )

class ClaudeTokenLimitError(ClaudeAPIError):
    """Error de límite de tokens de Claude"""
    def __init__(
        self, 
        message: str = "Token limit exceeded for Claude API",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message, 
            "CLAUDE_TOKEN_LIMIT_ERROR", 
            400, 
            details
        )

class ClaudeContentFilterError(ClaudeAPIError):
    """Error de filtro de contenido de Claude"""
    def __init__(
        self, 
        message: str = "Content filter triggered for Claude API",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message, 
            "CLAUDE_CONTENT_FILTER_ERROR", 
            400, 
            details
        )

class SearchAPIError(MCPClaudeError):
    """Error en la API de búsqueda"""
    def __init__(
        self, 
        message: str, 
        error_code: str = "SEARCH_API_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, status_code, details)

class FileSystemError(MCPClaudeError):
    """Error en operaciones de sistema de archivos"""
    def __init__(
        self, 
        message: str, 
        error_code: str = "FILESYSTEM_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, status_code, details)

class ValidationError(MCPClaudeError):
    """Error de validación"""
    def __init__(
        self, 
        message: str, 
        error_code: str = "VALIDATION_ERROR",
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, status_code, details)

class AuthenticationError(MCPClaudeError):
    """Error de autenticación"""
    def __init__(
        self, 
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message, 
            "AUTHENTICATION_ERROR", 
            401, 
            details
        )

class AuthorizationError(MCPClaudeError):
    """Error de autorización"""
    def __init__(
        self, 
        message: str = "Authorization failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message, 
            "AUTHORIZATION_ERROR", 
            403, 
            details
        )

class ResourceNotFoundError(MCPClaudeError):
    """Error de recurso no encontrado"""
    def __init__(
        self, 
        message: str = "Resource not found",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message, 
            "RESOURCE_NOT_FOUND", 
            404, 
            details
        )

async def mcp_claude_error_handler(request: Request, exc: MCPClaudeError) -> JSONResponse:
    """Manejador de errores para excepciones de MCP-Claude"""
    # Registrar el error
    LogManager.log_error(
        error_type=exc.error_code,
        error_message=exc.message,
        stack_trace=traceback.format_exc()
    )
    
    # Preparar respuesta
    error_response = {
        "error": {
            "code": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Manejador de errores para excepciones HTTP estándar"""
    # Registrar el error
    LogManager.log_error(
        error_type="HTTP_ERROR",
        error_message=str(exc.detail),
        stack_trace=traceback.format_exc()
    )
    
    # Preparar respuesta
    error_response = {
        "error": {
            "code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "details": {}
        }
    }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    ) 