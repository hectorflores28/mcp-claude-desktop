from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from enum import Enum

class ResourceType(str, Enum):
    """
    Tipos de recursos MCP
    """
    STATIC = "static"
    DYNAMIC = "dynamic"
    FILE = "file"
    API = "api"
    DATABASE = "database"
    CACHE = "cache"

class ResourceAccess(str, Enum):
    """
    Niveles de acceso a recursos
    """
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"

class ResourceDefinition(BaseModel):
    """
    Definición de un recurso MCP
    """
    name: str = Field(..., description="Nombre del recurso")
    type: ResourceType = Field(..., description="Tipo de recurso")
    description: str = Field(..., description="Descripción del recurso")
    access: List[ResourceAccess] = Field(..., description="Niveles de acceso permitidos")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Parámetros del recurso")
    dependencies: Optional[List[str]] = Field(None, description="Recursos de los que depende")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadatos adicionales")

class ResourceRequest(BaseModel):
    """
    Solicitud de acceso a un recurso
    """
    resource: str = Field(..., description="Nombre del recurso")
    action: ResourceAccess = Field(..., description="Acción a realizar")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Parámetros para la acción")
    context: Optional[Dict[str, Any]] = Field(None, description="Contexto adicional")

class ResourceResponse(BaseModel):
    """
    Respuesta de acceso a un recurso
    """
    success: bool = Field(..., description="Si la operación fue exitosa")
    data: Optional[Any] = Field(None, description="Datos devueltos por el recurso")
    error: Optional[Dict[str, Any]] = Field(None, description="Error si ocurre")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadatos adicionales")

class ResourcesResponse(BaseModel):
    """
    Respuesta con lista de recursos disponibles
    """
    resources: List[ResourceDefinition] = Field(..., description="Lista de recursos disponibles")

class ResourceCache(BaseModel):
    """
    Caché de recursos
    """
    resource: str = Field(..., description="Nombre del recurso")
    data: Any = Field(..., description="Datos cacheados")
    timestamp: str = Field(..., description="Marca de tiempo de la caché")
    ttl: int = Field(..., description="Tiempo de vida en segundos") 