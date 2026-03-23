"""
Endpoints para gestionar plugins.

Este módulo proporciona endpoints para gestionar los plugins del servidor MCP.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from pydantic import BaseModel

from app.core.plugins import plugin_manager
from app.core.config import settings
from app.core.logging import LogManager
from app.middleware.auth import verify_auth

router = APIRouter()
logger = LogManager.get_logger("api.plugins")

class PluginInfo(BaseModel):
    """Información de un plugin."""
    name: str
    version: str
    description: str
    enabled: bool

class PluginResponse(BaseModel):
    """Respuesta con información de plugins."""
    plugins: List[PluginInfo]
    total: int

@router.get("/", response_model=PluginResponse, tags=["plugins"])
async def list_plugins():
    """
    Lista todos los plugins disponibles.
    
    Returns:
        Lista de plugins disponibles
    """
    if not settings.PLUGINS_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los plugins están deshabilitados"
        )
    
    plugins = []
    for name, plugin in plugin_manager.plugins.items():
        plugins.append(
            PluginInfo(
                name=plugin.name,
                version=plugin.version,
                description=plugin.description,
                enabled=plugin.enabled
            )
        )
    
    return {
        "plugins": plugins,
        "total": len(plugins)
    }

@router.get("/{name}", response_model=PluginInfo, tags=["plugins"])
async def get_plugin(name: str):
    """
    Obtiene información de un plugin específico.
    
    Args:
        name: Nombre del plugin
        
    Returns:
        Información del plugin
    """
    if not settings.PLUGINS_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los plugins están deshabilitados"
        )
    
    plugin = plugin_manager.get_plugin(name)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{name}' no encontrado"
        )
    
    return PluginInfo(
        name=plugin.name,
        version=plugin.version,
        description=plugin.description,
        enabled=plugin.enabled
    )

@router.post("/{name}/enable", response_model=PluginInfo, tags=["plugins"])
async def enable_plugin(name: str):
    """
    Habilita un plugin.
    
    Args:
        name: Nombre del plugin
        
    Returns:
        Información del plugin habilitado
    """
    if not settings.PLUGINS_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los plugins están deshabilitados"
        )
    
    success = plugin_manager.enable_plugin(name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{name}' no encontrado"
        )
    
    plugin = plugin_manager.get_plugin(name)
    return PluginInfo(
        name=plugin.name,
        version=plugin.version,
        description=plugin.description,
        enabled=plugin.enabled
    )

@router.post("/{name}/disable", response_model=PluginInfo, tags=["plugins"])
async def disable_plugin(name: str):
    """
    Deshabilita un plugin.
    
    Args:
        name: Nombre del plugin
        
    Returns:
        Información del plugin deshabilitado
    """
    if not settings.PLUGINS_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los plugins están deshabilitados"
        )
    
    success = plugin_manager.disable_plugin(name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{name}' no encontrado"
        )
    
    plugin = plugin_manager.get_plugin(name)
    return PluginInfo(
        name=plugin.name,
        version=plugin.version,
        description=plugin.description,
        enabled=plugin.enabled
    )

@router.get("/hooks", response_model=List[str], tags=["plugins"])
async def list_hooks():
    """
    Lista todos los hooks disponibles.
    
    Returns:
        Lista de hooks disponibles
    """
    if not settings.PLUGINS_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los plugins están deshabilitados"
        )
    
    return settings.PLUGIN_HOOKS 