from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.core.security import verify_api_key
from app.core.logging import LogManager
from app.services.brave_search import BraveSearchService
from app.services.claude_service import ClaudeService
from app.services.filesystem_service import FileSystemService
import psutil
import os
from datetime import datetime

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/", response_model=Dict[str, Any])
async def health_check():
    """
    Verifica el estado general del servicio.
    
    Returns:
        Dict[str, Any]: Estado del servicio
    """
    try:
        # Obtener uso de recursos
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Verificar servicios
        brave_search = BraveSearchService()
        claude = ClaudeService()
        filesystem = FileSystemService()
        
        # Realizar verificaciones básicas
        services_status = {
            "brave_search": await brave_search.check_health(),
            "claude": await claude.check_health(),
            "filesystem": await filesystem.check_health()
        }
        
        # Construir respuesta
        status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "resources": {
                "cpu": {
                    "percent": cpu_percent,
                    "status": "ok" if cpu_percent < 80 else "warning"
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "status": "ok" if memory.percent < 80 else "warning"
                },
                "disk": {
                    "total": disk.total,
                    "free": disk.free,
                    "percent": disk.percent,
                    "status": "ok" if disk.percent < 80 else "warning"
                }
            },
            "services": services_status
        }
        
        # Verificar si hay algún servicio con problemas
        if any(service.get("status") != "ok" for service in services_status.values()):
            status["status"] = "degraded"
            
        # Registrar operación
        LogManager.log_info(f"Health check: {status['status']}")
        
        return status
        
    except Exception as e:
        LogManager.log_error("health", str(e))
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@router.get("/services", response_model=Dict[str, Any])
async def check_services(
    api_key: str = Depends(verify_api_key)
):
    """
    Verifica el estado de los servicios individuales.
    
    Args:
        api_key: API key para autenticación
        
    Returns:
        Dict[str, Any]: Estado de los servicios
    """
    try:
        # Inicializar servicios
        brave_search = BraveSearchService()
        claude = ClaudeService()
        filesystem = FileSystemService()
        
        # Verificar cada servicio
        services = {
            "brave_search": {
                "name": "Brave Search API",
                "status": await brave_search.check_health(),
                "last_check": datetime.now().isoformat()
            },
            "claude": {
                "name": "Claude API",
                "status": await claude.check_health(),
                "last_check": datetime.now().isoformat()
            },
            "filesystem": {
                "name": "File System",
                "status": await filesystem.check_health(),
                "last_check": datetime.now().isoformat()
            }
        }
        
        # Registrar operación
        LogManager.log_info("Verificación de servicios completada")
        
        return {
            "status": "ok",
            "services": services,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        LogManager.log_error("health", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error al verificar servicios: {str(e)}"
        )

@router.get("/resources", response_model=Dict[str, Any])
async def check_resources(
    api_key: str = Depends(verify_api_key)
):
    """
    Verifica el uso de recursos del sistema.
    
    Args:
        api_key: API key para autenticación
        
    Returns:
        Dict[str, Any]: Estado de los recursos
    """
    try:
        # Obtener métricas de recursos
        cpu = {
            "percent": psutil.cpu_percent(interval=1),
            "count": psutil.cpu_count(),
            "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        }
        
        memory = psutil.virtual_memory()._asdict()
        disk = psutil.disk_usage('/')._asdict()
        
        # Construir respuesta
        resources = {
            "cpu": cpu,
            "memory": memory,
            "disk": disk,
            "timestamp": datetime.now().isoformat()
        }
        
        # Registrar operación
        LogManager.log_info("Verificación de recursos completada")
        
        return resources
        
    except Exception as e:
        LogManager.log_error("health", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error al verificar recursos: {str(e)}"
        ) 