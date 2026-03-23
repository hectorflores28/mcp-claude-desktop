from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import LogManager
import time

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        LogManager.log_api_request(
            method=request.method,
            path=request.url.path,
            data=await request.json() if request.method in ["POST", "PUT"] else None
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Log response
        LogManager.log_api_response(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            response_time=response_time
        )
        
        return response

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            LogManager.log_error(
                error_type=type(e).__name__,
                error_message=str(e),
                stack_trace=str(e.__traceback__)
            )
            raise 