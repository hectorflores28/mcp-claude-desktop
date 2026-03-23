from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class MCPVersion(str, Enum):
    """
    Versiones soportadas del protocolo MCP
    """
    V1_0 = "1.0"
    V1_1 = "1.1"
    V1_2 = "1.2"

class MCPFeature(str, Enum):
    """
    Características soportadas por el protocolo MCP
    """
    RESOURCES = "resources"
    TOOLS = "tools"
    FILESYSTEM = "filesystem"
    CACHE = "cache"
    LOGGING = "logging"
    PROMPTS = "prompts"
    METRICS = "metrics"
    AUTHENTICATION = "authentication"

class MCPResourceType(str, Enum):
    """
    Tipos de recursos soportados
    """
    STATIC = "static"
    API = "api"
    CACHE = "cache"
    FILE = "file"
    DATABASE = "database"

class MCPAccessLevel(str, Enum):
    """
    Niveles de acceso soportados
    """
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"

class MCPConfig(BaseModel):
    """
    Configuración global del protocolo MCP
    """
    version: MCPVersion = Field(MCPVersion.V1_1, description="Versión del protocolo MCP")
    features: List[MCPFeature] = Field(
        default=[
            MCPFeature.RESOURCES,
            MCPFeature.TOOLS,
            MCPFeature.FILESYSTEM,
            MCPFeature.CACHE,
            MCPFeature.LOGGING,
            MCPFeature.PROMPTS
        ],
        description="Características soportadas"
    )
    resource_types: List[MCPResourceType] = Field(
        default=[
            MCPResourceType.STATIC,
            MCPResourceType.API,
            MCPResourceType.CACHE,
            MCPResourceType.FILE
        ],
        description="Tipos de recursos soportados"
    )
    access_levels: List[MCPAccessLevel] = Field(
        default=[
            MCPAccessLevel.READ,
            MCPAccessLevel.WRITE,
            MCPAccessLevel.EXECUTE,
            MCPAccessLevel.ADMIN
        ],
        description="Niveles de acceso soportados"
    )
    max_request_size: int = Field(1048576, description="Tamaño máximo de solicitud en bytes")
    max_response_size: int = Field(10485760, description="Tamaño máximo de respuesta en bytes")
    timeout: int = Field(30, description="Tiempo de espera en segundos")
    rate_limit: int = Field(60, description="Límite de solicitudes por minuto")
    cache_ttl: int = Field(3600, description="Tiempo de vida de caché en segundos")
    log_level: str = Field("INFO", description="Nivel de logging")
    debug: bool = Field(False, description="Modo debug")

class MCPResourceConfig(BaseModel):
    """
    Configuración de un recurso MCP
    """
    name: str = Field(..., description="Nombre del recurso")
    type: MCPResourceType = Field(..., description="Tipo de recurso")
    access: List[MCPAccessLevel] = Field(..., description="Niveles de acceso permitidos")
    parameters: Dict[str, Any] = Field(..., description="Parámetros del recurso")
    cache_enabled: bool = Field(False, description="Si el recurso usa caché")
    cache_ttl: Optional[int] = Field(None, description="Tiempo de vida de caché en segundos")
    rate_limit: Optional[int] = Field(None, description="Límite de solicitudes por minuto")
    timeout: Optional[int] = Field(None, description="Tiempo de espera en segundos")

class MCPToolConfig(BaseModel):
    """
    Configuración de una herramienta MCP
    """
    name: str = Field(..., description="Nombre de la herramienta")
    description: str = Field(..., description="Descripción de la herramienta")
    parameters: Dict[str, Any] = Field(..., description="Esquema de parámetros de la herramienta")
    required_resources: List[str] = Field(default=[], description="Recursos requeridos")
    cache_enabled: bool = Field(True, description="Si la herramienta usa caché")
    cache_ttl: Optional[int] = Field(None, description="Tiempo de vida de caché en segundos")
    rate_limit: Optional[int] = Field(None, description="Límite de solicitudes por minuto")
    timeout: Optional[int] = Field(None, description="Tiempo de espera en segundos")

# Configuración global
mcp_config = MCPConfig()

# Recursos predefinidos
mcp_resources: Dict[str, MCPResourceConfig] = {
    "filesystem": MCPResourceConfig(
        name="filesystem",
        type=MCPResourceType.STATIC,
        access=[MCPAccessLevel.READ, MCPAccessLevel.WRITE, MCPAccessLevel.EXECUTE],
        parameters={
            "operations": ["create", "read", "update", "delete", "list"],
            "allowed_extensions": ["md", "txt", "json", "py", "js", "html", "css"],
            "max_file_size": 10485760  # 10MB
        },
        cache_enabled=True,
        cache_ttl=300  # 5 minutos
    ),
    "claude": MCPResourceConfig(
        name="claude",
        type=MCPResourceType.API,
        access=[MCPAccessLevel.EXECUTE],
        parameters={
            "operations": ["completion", "analyze", "generate"],
            "model": "claude-3-opus-20240229",
            "max_tokens": 4096,
            "temperature": 0.7
        },
        cache_enabled=True,
        cache_ttl=3600,  # 1 hora
        rate_limit=30  # 30 solicitudes por minuto
    ),
    "search": MCPResourceConfig(
        name="search",
        type=MCPResourceType.API,
        access=[MCPAccessLevel.EXECUTE],
        parameters={
            "operations": ["search", "analyze"],
            "default_results": 5,
            "default_country": "ES",
            "default_language": "es"
        },
        cache_enabled=True,
        cache_ttl=1800,  # 30 minutos
        rate_limit=20  # 20 solicitudes por minuto
    ),
    "cache": MCPResourceConfig(
        name="cache",
        type=MCPResourceType.CACHE,
        access=[MCPAccessLevel.READ, MCPAccessLevel.WRITE],
        parameters={
            "operations": ["get", "set", "delete", "clear"],
            "default_ttl": 3600  # 1 hora
        },
        cache_enabled=False
    )
}

# Herramientas predefinidas
mcp_tools: Dict[str, MCPToolConfig] = {
    "buscar_en_brave": MCPToolConfig(
        name="buscar_en_brave",
        description="Realiza una búsqueda web usando Brave Search",
        parameters={
            "query": {"type": "string", "description": "Término de búsqueda"},
            "num_results": {"type": "integer", "description": "Número de resultados", "default": 5},
            "analyze": {"type": "boolean", "description": "Analizar resultados", "default": False}
        },
        required_resources=["search"],
        cache_enabled=True,
        cache_ttl=1800,  # 30 minutos
        rate_limit=20  # 20 solicitudes por minuto
    ),
    "generar_markdown": MCPToolConfig(
        name="generar_markdown",
        description="Genera contenido en formato Markdown",
        parameters={
            "content": {"type": "string", "description": "Contenido a formatear"},
            "format_type": {"type": "string", "description": "Tipo de formato", "default": "article"},
            "save": {"type": "boolean", "description": "Guardar en archivo", "default": False},
            "filename": {"type": "string", "description": "Nombre del archivo", "default": "output.md"}
        },
        required_resources=["claude", "filesystem"],
        cache_enabled=True,
        cache_ttl=3600  # 1 hora
    ),
    "analizar_texto": MCPToolConfig(
        name="analizar_texto",
        description="Analiza texto usando Claude",
        parameters={
            "text": {"type": "string", "description": "Texto a analizar"},
            "analysis_type": {"type": "string", "description": "Tipo de análisis", "default": "summary"}
        },
        required_resources=["claude"],
        cache_enabled=True,
        cache_ttl=3600  # 1 hora
    )
} 