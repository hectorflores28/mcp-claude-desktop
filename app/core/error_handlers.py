from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import MCPClaudeError
from app.core.logging import LogManager

async def mcp_claude_error_handler(request: Request, exc: MCPClaudeError):
    """
    Manejador global de errores para excepciones de MCP Claude
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )

async def http_exception_handler(request: Request, exc: Exception):
    """
    Manejador global para excepciones HTTP genéricas
    """
    LogManager.log_error(
        "Error HTTP no manejado",
        error=exc,
        extra={"path": request.url.path, "method": request.method}
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {"type": exc.__class__.__name__}
            }
        }
    ) 