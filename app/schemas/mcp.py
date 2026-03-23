from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class MCPVersion(str, Enum):
    """
    Versiones soportadas del protocolo MCP
    """
    V1_0 = "1.0"
    V1_1 = "1.1"
    V1_2 = "1.2"

class MCPMethod(str, Enum):
    """
    Métodos soportados por el protocolo MCP
    """
    LIST_RESOURCES = "list_resources"
    ACCESS = "access"
    EXECUTE = "execute"
    STATUS = "status"

class MCPRequest(BaseModel):
    """
    Modelo de solicitud MCP
    """
    jsonrpc: str = Field("2.0", description="Versión de JSON-RPC")
    method: str = Field(..., description="Método a ejecutar")
    params: Dict[str, Any] = Field(..., description="Parámetros del método")
    id: Optional[str] = Field(None, description="Identificador de la solicitud")
    version: MCPVersion = Field(MCPVersion.V1_1, description="Versión del protocolo MCP")

class MCPResponse(BaseModel):
    """
    Modelo de respuesta MCP
    """
    jsonrpc: str = Field("2.0", description="Versión de JSON-RPC")
    result: Optional[Any] = Field(None, description="Resultado de la operación")
    error: Optional["MCPError"] = Field(None, description="Error de la operación")
    id: Optional[str] = Field(None, description="Identificador de la solicitud")
    execution_time: float = Field(..., description="Tiempo de ejecución en segundos")

class MCPError(BaseModel):
    """
    Modelo de error MCP
    """
    code: int = Field(..., description="Código de error")
    message: str = Field(..., description="Mensaje de error")
    data: Optional[Dict[str, Any]] = Field(None, description="Datos adicionales del error")

class MCPStatus(BaseModel):
    """
    Modelo de estado MCP
    """
    version: MCPVersion = Field(..., description="Versión del protocolo MCP")
    features: List[str] = Field(..., description="Características soportadas")
    resource_types: List[str] = Field(..., description="Tipos de recursos soportados")
    access_levels: List[str] = Field(..., description="Niveles de acceso soportados")
    resources: List[str] = Field(..., description="Recursos disponibles")
    tools: List[str] = Field(..., description="Herramientas disponibles")
    timestamp: str = Field(..., description="Marca de tiempo del estado")

class MCPOperation(BaseModel):
    """
    Modelo de operación MCP
    """
    method: str = Field(..., description="Método ejecutado")
    params: Dict[str, Any] = Field(..., description="Parámetros utilizados")
    timestamp: str = Field(..., description="Marca de tiempo de la operación")
    status: Optional[str] = Field(None, description="Estado de la operación")
    error: Optional[MCPError] = Field(None, description="Error de la operación")
    execution_time: Optional[float] = Field(None, description="Tiempo de ejecución en segundos")

class MCPExecuteRequest(BaseModel):
    """
    Modelo de solicitud de ejecución MCP
    """
    tool: str = Field(..., description="Nombre de la herramienta a ejecutar")
    params: Dict[str, Any] = Field(..., description="Parámetros de la herramienta")

class MCPExecuteResponse(BaseModel):
    """
    Modelo de respuesta de ejecución MCP
    """
    result: Any = Field(..., description="Resultado de la ejecución")
    cached: bool = Field(False, description="Si el resultado proviene de caché")
    execution_time: float = Field(..., description="Tiempo de ejecución en segundos")

class MCPPromptTemplate(BaseModel):
    """
    Modelo de plantilla de prompt MCP
    """
    name: str = Field(..., description="Nombre de la plantilla")
    description: str = Field(..., description="Descripción de la plantilla")
    template: str = Field(..., description="Plantilla de prompt")
    parameters: Dict[str, Any] = Field(..., description="Parámetros de la plantilla")
    version: MCPVersion = Field(MCPVersion.V1_1, description="Versión del protocolo MCP")

class MCPPromptTemplatesResponse(BaseModel):
    """
    Modelo de respuesta de plantillas de prompt MCP
    """
    templates: List[MCPPromptTemplate] = Field(..., description="Plantillas disponibles")
    version: MCPVersion = Field(MCPVersion.V1_1, description="Versión del protocolo MCP")

class ToolDefinition(BaseModel):
    """
    Definición de una herramienta MCP
    """
    name: str = Field(..., description="Nombre de la herramienta")
    description: str = Field(..., description="Descripción de la herramienta")
    parameters: Dict[str, Any] = Field(..., description="Esquema de parámetros de la herramienta")
    required_resources: List[str] = Field(default=[], description="Recursos requeridos")
    cache_enabled: bool = Field(default=True, description="Si la herramienta usa caché")
    cache_ttl: Optional[int] = Field(default=None, description="Tiempo de vida de caché en segundos")
    rate_limit: Optional[int] = Field(default=None, description="Límite de solicitudes por minuto")
    timeout: Optional[int] = Field(default=None, description="Tiempo de espera en segundos")

class MCPToolsResponse(BaseModel):
    """
    Respuesta con lista de herramientas disponibles
    """
    tools: List[ToolDefinition] = Field(..., description="Lista de herramientas disponibles")
    version: str = Field("1.1", description="Versión del protocolo MCP") 