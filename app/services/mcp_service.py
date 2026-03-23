from typing import Dict, List, Optional, Any, Union
import time
import json
from datetime import datetime, timedelta
import logging

from app.core.mcp_config import (
    mcp_config, mcp_resources, mcp_tools, 
    MCPVersion, MCPFeature, MCPResourceType, MCPAccessLevel
)
from app.schemas.mcp import (
    MCPRequest, MCPResponse, MCPError, MCPStatus, 
    MCPOperation, MCPExecuteRequest, MCPExecuteResponse, MCPMethod
)
from app.services.resources_service import ResourcesService
from app.services.filesystem_service import FileSystemService
from app.services.claude_service import ClaudeService
from app.services.cache import CacheService
from app.core.logging import LogManager
from app.core.cache import cache

logger = logging.getLogger(__name__)

class MCPService:
    """
    Servicio principal para el protocolo MCP
    """
    def __init__(self):
        """
        Inicializa el servicio MCP.
        """
        self.resources_service = ResourcesService()
        self.filesystem_service = FileSystemService()
        self.claude_service = ClaudeService()
        self.cache_service = CacheService()
        self.operations: List[MCPOperation] = []
        self._rate_limit_cache: Dict[str, Dict[str, int]] = {}
        self._last_cleanup = time.time()
        LogManager.log_info("mcp", "Servicio MCP inicializado")
        
    async def get_status(self) -> MCPStatus:
        """
        Obtiene el estado actual del protocolo MCP.
        
        Returns:
            Estado del protocolo MCP
        """
        # Intentar obtener del caché
        cache_key = "mcp:status"
        cached_status = cache.get(cache_key)
        
        if cached_status:
            LogManager.log_info("mcp", "Estado MCP obtenido del caché")
            return MCPStatus(**cached_status)
        
        # Si no está en caché, crear nuevo estado
        status = MCPStatus(
            version=MCPVersion.V1_1,
            features=["resources", "tools", "filesystem", "cache", "logging", "prompts"],
            resource_types=["filesystem", "claude", "search", "cache"],
            access_levels=["read", "write", "admin"],
            resources={
                "filesystem": {
                    "type": "filesystem",
                    "operations": ["create", "read", "update", "delete", "list"],
                    "access_level": "write"
                },
                "claude": {
                    "type": "claude",
                    "operations": ["completion", "analyze", "generate"],
                    "access_level": "read"
                },
                "search": {
                    "type": "search",
                    "operations": ["execute", "analyze"],
                    "access_level": "read"
                },
                "cache": {
                    "type": "cache",
                    "operations": ["get", "set", "delete", "clear"],
                    "access_level": "write"
                }
            },
            tools={
                "buscar_en_brave": {
                    "name": "buscar_en_brave",
                    "description": "Realiza una búsqueda web usando Brave Search",
                    "parameters": {
                        "query": {"type": "string", "description": "Consulta de búsqueda", "required": True},
                        "num_results": {"type": "integer", "description": "Número de resultados", "required": False, "default": 5},
                        "analysis": {"type": "boolean", "description": "Analizar resultados", "required": False, "default": False}
                    },
                    "required_resources": ["search"],
                    "cache_enabled": True,
                    "cache_ttl": 3600,
                    "rate_limit": 10,
                    "timeout": 30
                },
                "generar_markdown": {
                    "name": "generar_markdown",
                    "description": "Genera contenido en formato Markdown",
                    "parameters": {
                        "content": {"type": "string", "description": "Contenido a formatear", "required": True},
                        "format": {"type": "string", "description": "Tipo de formato", "required": False, "default": "basic"},
                        "save": {"type": "boolean", "description": "Guardar archivo", "required": False, "default": False},
                        "filename": {"type": "string", "description": "Nombre del archivo", "required": False}
                    },
                    "required_resources": ["filesystem"],
                    "cache_enabled": False,
                    "rate_limit": 20,
                    "timeout": 15
                },
                "analizar_texto": {
                    "name": "analizar_texto",
                    "description": "Analiza texto usando Claude",
                    "parameters": {
                        "text": {"type": "string", "description": "Texto a analizar", "required": True},
                        "analysis_type": {"type": "string", "description": "Tipo de análisis", "required": False, "default": "general"}
                    },
                    "required_resources": ["claude"],
                    "cache_enabled": True,
                    "cache_ttl": 86400,
                    "rate_limit": 5,
                    "timeout": 60
                }
            },
            timestamp=datetime.now().isoformat()
        )
        
        # Guardar en caché por 5 minutos
        cache.set(cache_key, status.dict(), expire=300)
        
        return status
    
    def _check_rate_limit(self, request: MCPRequest) -> bool:
        """
        Verifica si se ha excedido el límite de tasa para un método o herramienta
        """
        current_time = time.time()
        
        # Limpiar caché antigua cada 5 minutos
        if current_time - self._last_cleanup > 300:
            self._rate_limit_cache = {}
            self._last_cleanup = current_time
        
        # Obtener límite de tasa
        rate_limit = mcp_config.rate_limit
        
        # Verificar límite específico para herramientas
        if request.method == "execute" and "tool" in request.params:
            tool_name = request.params.get("tool")
            if tool_name in mcp_tools and mcp_tools[tool_name].rate_limit:
                rate_limit = mcp_tools[tool_name].rate_limit
        
        # Verificar límite específico para recursos
        if request.method == "access" and "resource" in request.params:
            resource_name = request.params.get("resource")
            if resource_name in mcp_resources and mcp_resources[resource_name].rate_limit:
                rate_limit = mcp_resources[resource_name].rate_limit
        
        # Crear clave para el caché
        cache_key = f"{request.method}:{json.dumps(request.params, sort_keys=True)}"
        
        # Inicializar contador si no existe
        if cache_key not in self._rate_limit_cache:
            self._rate_limit_cache[cache_key] = {
                "count": 0,
                "reset_time": current_time + 60
            }
        
        # Reiniciar contador si ha pasado el tiempo
        if current_time > self._rate_limit_cache[cache_key]["reset_time"]:
            self._rate_limit_cache[cache_key] = {
                "count": 0,
                "reset_time": current_time + 60
            }
        
        # Incrementar contador
        self._rate_limit_cache[cache_key]["count"] += 1
        
        # Verificar si se excedió el límite
        return self._rate_limit_cache[cache_key]["count"] <= rate_limit
    
    def validate_request(self, request: MCPRequest) -> Optional[MCPError]:
        """
        Valida una solicitud MCP
        """
        # Verificar campos requeridos
        if not request.method:
            return MCPError(code=400, message="El campo 'method' es requerido")
        
        if not request.params:
            return MCPError(code=400, message="El campo 'params' es requerido")
        
        # Verificar tamaño de la solicitud
        request_size = len(json.dumps(request.dict()).encode())
        if request_size > mcp_config.max_request_size:
            return MCPError(
                code=413, 
                message=f"La solicitud excede el tamaño máximo permitido de {mcp_config.max_request_size} bytes"
            )
        
        # Verificar límite de tasa
        if not self._check_rate_limit(request):
            return MCPError(code=429, message="Se ha excedido el límite de solicitudes")
        
        return None
    
    async def process_request(self, request: MCPRequest) -> MCPResponse:
        """
        Procesa una solicitud MCP
        """
        start_time = time.time()
        
        # Registrar operación
        operation = MCPOperation(
            method=request.method,
            params=request.params,
            timestamp=datetime.now().isoformat()
        )
        self.operations.append(operation)
        
        # Validar solicitud
        error = self.validate_request(request)
        if error:
            operation.status = "error"
            operation.error = error
            return MCPResponse(
                id=request.id,
                result=None,
                error=error,
                execution_time=time.time() - start_time
            )
        
        # Procesar según el método
        try:
            result = None
            
            if request.method == "list_resources":
                result = await self.resources_service.list_resources()
            
            elif request.method == "access":
                resource_name = request.params.get("resource")
                operation_name = request.params.get("operation")
                params = request.params.get("params", {})
                
                if not resource_name:
                    raise ValueError("El parámetro 'resource' es requerido")
                
                if not operation_name:
                    raise ValueError("El parámetro 'operation' es requerido")
                
                result = await self.resources_service.access_resource(
                    resource_name, operation_name, params
                )
            
            elif request.method == "execute":
                tool_name = request.params.get("tool")
                params = request.params.get("params", {})
                
                if not tool_name:
                    raise ValueError("El parámetro 'tool' es requerido")
                
                result = await self._execute_tool(tool_name, params)
            
            else:
                raise ValueError(f"Método no soportado: {request.method}")
            
            # Verificar tamaño de la respuesta
            response_size = len(json.dumps(result).encode())
            if response_size > mcp_config.max_response_size:
                raise ValueError(
                    f"La respuesta excede el tamaño máximo permitido de {mcp_config.max_response_size} bytes"
                )
            
            operation.status = "success"
            return MCPResponse(
                id=request.id,
                result=result,
                error=None,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Error procesando solicitud MCP: {str(e)}", exc_info=True)
            operation.status = "error"
            operation.error = MCPError(code=500, message=str(e))
            return MCPResponse(
                id=request.id,
                result=None,
                error=operation.error,
                execution_time=time.time() - start_time
            )
    
    async def _execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """
        Ejecuta una herramienta MCP
        """
        if tool_name not in mcp_tools:
            raise ValueError(f"Herramienta no encontrada: {tool_name}")
        
        tool_config = mcp_tools[tool_name]
        
        # Verificar recursos requeridos
        for resource_name in tool_config.required_resources:
            if resource_name not in mcp_resources:
                raise ValueError(f"Recurso requerido no encontrado: {resource_name}")
        
        # Verificar caché
        if tool_config.cache_enabled:
            cache_key = f"tool:{tool_name}:{json.dumps(params, sort_keys=True)}"
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                return cached_result
        
        # Ejecutar herramienta
        result = None
        
        if tool_name == "buscar_en_brave":
            result = await self._execute_search(params)
        
        elif tool_name == "generar_markdown":
            result = await self._execute_markdown(params)
        
        elif tool_name == "analizar_texto":
            result = await self._execute_analysis(params)
        
        else:
            raise ValueError(f"Herramienta no implementada: {tool_name}")
        
        # Guardar en caché
        if tool_config.cache_enabled and result:
            cache_key = f"tool:{tool_name}:{json.dumps(params, sort_keys=True)}"
            cache_ttl = tool_config.cache_ttl or mcp_config.cache_ttl
            await self.cache_service.set(cache_key, result, cache_ttl)
        
        return result
    
    async def _execute_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta la herramienta de búsqueda
        """
        query = params.get("query")
        num_results = params.get("num_results", 5)
        analyze = params.get("analyze", False)
        
        if not query:
            raise ValueError("El parámetro 'query' es requerido")
        
        # Realizar búsqueda
        search_results = await self.resources_service.access_resource(
            "search", "search", {"query": query, "num_results": num_results}
        )
        
        # Analizar resultados si se solicita
        if analyze and search_results:
            analysis = await self.resources_service.access_resource(
                "search", "analyze", {"results": search_results}
            )
            return {
                "results": search_results,
                "analysis": analysis
            }
        
        return {"results": search_results}
    
    async def _execute_markdown(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta la herramienta de generación de Markdown
        """
        content = params.get("content")
        format_type = params.get("format_type", "article")
        save = params.get("save", False)
        filename = params.get("filename", "output.md")
        
        if not content:
            raise ValueError("El parámetro 'content' es requerido")
        
        # Generar Markdown
        markdown = await self.resources_service.access_resource(
            "claude", "generate", {
                "text": content,
                "format": format_type
            }
        )
        
        # Guardar en archivo si se solicita
        if save:
            await self.resources_service.access_resource(
                "filesystem", "write", {
                    "filename": filename,
                    "content": markdown
                }
            )
            return {
                "markdown": markdown,
                "saved": True,
                "filename": filename
            }
        
        return {"markdown": markdown, "saved": False}
    
    async def _execute_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta la herramienta de análisis de texto
        """
        text = params.get("text")
        analysis_type = params.get("analysis_type", "summary")
        
        if not text:
            raise ValueError("El parámetro 'text' es requerido")
        
        # Analizar texto
        analysis = await self.resources_service.access_resource(
            "claude", "analyze", {
                "text": text,
                "analysis_type": analysis_type
            }
        )
        
        return {"analysis": analysis}
    
    async def get_recent_operations(self, limit: int = 10) -> List[MCPOperation]:
        """
        Obtiene las operaciones más recientes
        """
        return sorted(
            self.operations, 
            key=lambda x: x.timestamp, 
            reverse=True
        )[:limit] 