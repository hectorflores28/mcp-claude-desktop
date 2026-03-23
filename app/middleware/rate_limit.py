from fastapi import Request, HTTPException, status
from app.core.cache import cache
from app.core.config import settings
from app.core.logging import LogManager
import time
import json
from typing import Optional, Dict, Any

class RateLimiter:
    """
    Clase para manejar el rate limiting basado en IP
    """
    
    def __init__(self):
        """
        Inicializa el rate limiter
        """
        self.window = settings.RATE_LIMIT_WINDOW
        self.max_requests = settings.RATE_LIMIT_MAX_REQUESTS
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Obtiene la IP del cliente
        
        Args:
            request: Solicitud HTTP
            
        Returns:
            IP del cliente
        """
        # Intentar obtener la IP real detrás de un proxy
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Obtener la IP del cliente
        return request.client.host if request.client else "unknown"
    
    def _get_cache_key(self, ip: str, endpoint: str) -> str:
        """
        Genera una clave para el caché
        
        Args:
            ip: IP del cliente
            endpoint: Endpoint solicitado
            
        Returns:
            Clave para el caché
        """
        return f"rate_limit:{ip}:{endpoint}"
    
    def _get_current_window(self, ip: str, endpoint: str) -> Dict[str, Any]:
        """
        Obtiene la ventana actual de rate limiting
        
        Args:
            ip: IP del cliente
            endpoint: Endpoint solicitado
            
        Returns:
            Datos de la ventana actual
        """
        cache_key = self._get_cache_key(ip, endpoint)
        data = cache.get(cache_key)
        
        if not data:
            # Crear nueva ventana
            data = {
                "count": 0,
                "reset_time": int(time.time()) + self.window
            }
            cache.set(cache_key, data, expire=self.window)
        
        return data
    
    def _update_window(self, ip: str, endpoint: str, data: Dict[str, Any]) -> None:
        """
        Actualiza la ventana de rate limiting
        
        Args:
            ip: IP del cliente
            endpoint: Endpoint solicitado
            data: Datos de la ventana actual
        """
        cache_key = self._get_cache_key(ip, endpoint)
        cache.set(cache_key, data, expire=self.window)
    
    async def check_rate_limit(self, request: Request) -> None:
        """
        Verifica si se ha excedido el límite de tasa
        
        Args:
            request: Solicitud HTTP
            
        Raises:
            HTTPException: Si se ha excedido el límite de tasa
        """
        # Obtener la IP del cliente
        ip = self._get_client_ip(request)
        
        # Obtener el endpoint solicitado
        endpoint = request.url.path
        
        # Obtener la ventana actual
        data = self._get_current_window(ip, endpoint)
        
        # Verificar si la ventana ha expirado
        current_time = int(time.time())
        if current_time > data["reset_time"]:
            # Reiniciar ventana
            data = {
                "count": 0,
                "reset_time": current_time + self.window
            }
        
        # Incrementar contador
        data["count"] += 1
        
        # Actualizar ventana
        self._update_window(ip, endpoint, data)
        
        # Verificar si se ha excedido el límite
        if data["count"] > self.max_requests:
            # Calcular tiempo restante
            reset_time = data["reset_time"] - current_time
            
            # Registrar exceso
            LogManager.log_warning(
                "rate_limit", 
                f"IP {ip} excedió el límite de tasa para {endpoint}"
            )
            
            # Lanzar excepción
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "message": "Se ha excedido el límite de solicitudes",
                    "reset_in": reset_time
                },
                headers={
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": str(max(0, self.max_requests - data["count"])),
                    "X-RateLimit-Reset": str(data["reset_time"]),
                    "Retry-After": str(reset_time)
                }
            )

# Instancia global del rate limiter
rate_limiter = RateLimiter()

async def rate_limit_middleware(request: Request, call_next):
    """
    Middleware para rate limiting
    
    Args:
        request: Solicitud HTTP
        call_next: Función para llamar al siguiente middleware
        
    Returns:
        Respuesta HTTP
    """
    # Verificar si la ruta es pública
    if request.url.path in ["/api/health", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)
    
    # Verificar rate limit
    await rate_limiter.check_rate_limit(request)
    
    # Continuar con la solicitud
    return await call_next(request) 