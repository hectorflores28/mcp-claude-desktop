from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import os
from app.core.config import settings
from app.core.logging import LogManager
from app.schemas.resources import (
    ResourceDefinition,
    ResourceType,
    ResourceAccess,
    ResourceRequest,
    ResourceResponse,
    ResourcesResponse,
    ResourceCache
)
from app.services.filesystem_service import FileSystemService
from app.services.claude_service import ClaudeService
from app.services.cache import CacheService

class ResourcesService:
    """
    Servicio para gestionar recursos MCP
    """
    def __init__(self):
        self.resources: Dict[str, ResourceDefinition] = {}
        self.cache_service = CacheService()
        self.filesystem_service = FileSystemService()
        self.claude_service = ClaudeService()
        self._load_resources()
    
    def _load_resources(self) -> None:
        """
        Carga los recursos disponibles
        """
        # Recursos estáticos
        self.resources["filesystem"] = ResourceDefinition(
            name="filesystem",
            type=ResourceType.STATIC,
            description="Sistema de archivos para operaciones CRUD",
            access=[ResourceAccess.READ, ResourceAccess.WRITE, ResourceAccess.EXECUTE],
            parameters={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["create", "read", "update", "delete", "list"],
                        "description": "Operación a realizar"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Nombre del archivo"
                    },
                    "content": {
                        "type": "string",
                        "description": "Contenido del archivo (para create/update)"
                    }
                },
                "required": ["operation"]
            }
        )
        
        self.resources["claude"] = ResourceDefinition(
            name="claude",
            type=ResourceType.API,
            description="API de Claude para generación y análisis de texto",
            access=[ResourceAccess.EXECUTE],
            parameters={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["completion", "analyze", "generate"],
                        "description": "Operación a realizar"
                    },
                    "text": {
                        "type": "string",
                        "description": "Texto a procesar"
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Número máximo de tokens",
                        "default": 4096
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Temperatura para la generación",
                        "default": 0.7
                    }
                },
                "required": ["operation", "text"]
            }
        )
        
        self.resources["search"] = ResourceDefinition(
            name="search",
            type=ResourceType.API,
            description="API de búsqueda web",
            access=[ResourceAccess.READ],
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Término de búsqueda"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Número de resultados",
                        "default": 5
                    },
                    "analyze": {
                        "type": "boolean",
                        "description": "Si se debe analizar los resultados",
                        "default": False
                    }
                },
                "required": ["query"]
            }
        )
        
        self.resources["cache"] = ResourceDefinition(
            name="cache",
            type=ResourceType.CACHE,
            description="Sistema de caché para recursos",
            access=[ResourceAccess.READ, ResourceAccess.WRITE],
            parameters={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Clave de caché"
                    },
                    "value": {
                        "type": "any",
                        "description": "Valor a almacenar"
                    },
                    "ttl": {
                        "type": "integer",
                        "description": "Tiempo de vida en segundos",
                        "default": 3600
                    }
                },
                "required": ["key"]
            }
        )
        
        # Registrar recursos cargados
        LogManager.log_info(f"Cargados {len(self.resources)} recursos MCP")
    
    async def list_resources(self) -> ResourcesResponse:
        """
        Lista todos los recursos disponibles
        
        Returns:
            ResourcesResponse con la lista de recursos
        """
        return ResourcesResponse(resources=list(self.resources.values()))
    
    async def get_resource(self, name: str) -> Optional[ResourceDefinition]:
        """
        Obtiene un recurso por nombre
        
        Args:
            name: Nombre del recurso
            
        Returns:
            ResourceDefinition si existe, None en caso contrario
        """
        return self.resources.get(name)
    
    async def access_resource(self, request: ResourceRequest) -> ResourceResponse:
        """
        Accede a un recurso
        
        Args:
            request: Solicitud de acceso al recurso
            
        Returns:
            ResourceResponse con el resultado del acceso
        """
        try:
            # Verificar que el recurso existe
            resource = self.resources.get(request.resource)
            if not resource:
                return ResourceResponse(
                    success=False,
                    error={"code": 404, "message": f"Recurso no encontrado: {request.resource}"}
                )
            
            # Verificar que la acción está permitida
            if request.action not in resource.access:
                return ResourceResponse(
                    success=False,
                    error={"code": 403, "message": f"Acción no permitida: {request.action}"}
                )
            
            # Procesar según el tipo de recurso
            if resource.type == ResourceType.STATIC:
                return await self._handle_static_resource(resource, request)
            elif resource.type == ResourceType.API:
                return await self._handle_api_resource(resource, request)
            elif resource.type == ResourceType.CACHE:
                return await self._handle_cache_resource(resource, request)
            else:
                return ResourceResponse(
                    success=False,
                    error={"code": 501, "message": f"Tipo de recurso no soportado: {resource.type}"}
                )
                
        except Exception as e:
            LogManager.log_error("resources", str(e))
            return ResourceResponse(
                success=False,
                error={"code": 500, "message": f"Error al acceder al recurso: {str(e)}"}
            )
    
    async def _handle_static_resource(
        self,
        resource: ResourceDefinition,
        request: ResourceRequest
    ) -> ResourceResponse:
        """
        Maneja un recurso estático
        
        Args:
            resource: Definición del recurso
            request: Solicitud de acceso
            
        Returns:
            ResourceResponse con el resultado
        """
        if resource.name == "filesystem":
            operation = request.parameters.get("operation")
            filename = request.parameters.get("filename")
            content = request.parameters.get("content")
            
            if operation == "create":
                result = await self.filesystem_service.save_file(content, filename)
            elif operation == "read":
                result = await self.filesystem_service.read_file(filename)
            elif operation == "list":
                result = await self.filesystem_service.list_files()
            elif operation == "update":
                result = await self.filesystem_service.update_file(filename, content)
            elif operation == "delete":
                result = await self.filesystem_service.delete_file(filename)
            else:
                return ResourceResponse(
                    success=False,
                    error={"code": 400, "message": f"Operación no válida: {operation}"}
                )
            
            return ResourceResponse(
                success=result.success,
                data=result.dict(),
                error=result.error
            )
        
        return ResourceResponse(
            success=False,
            error={"code": 404, "message": f"Recurso estático no encontrado: {resource.name}"}
        )
    
    async def _handle_api_resource(
        self,
        resource: ResourceDefinition,
        request: ResourceRequest
    ) -> ResourceResponse:
        """
        Maneja un recurso de API
        
        Args:
            resource: Definición del recurso
            request: Solicitud de acceso
            
        Returns:
            ResourceResponse con el resultado
        """
        if resource.name == "claude":
            operation = request.parameters.get("operation")
            text = request.parameters.get("text")
            max_tokens = request.parameters.get("max_tokens", 4096)
            temperature = request.parameters.get("temperature", 0.7)
            
            if operation == "completion":
                result = await self.claude_service.mcp_completion(
                    prompt=text,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            elif operation == "analyze":
                result = await self.claude_service.analyze_text(
                    text=text,
                    analysis_type="summary"
                )
            elif operation == "generate":
                result = await self.claude_service.generate_markdown(
                    content=text,
                    format_type="article"
                )
            else:
                return ResourceResponse(
                    success=False,
                    error={"code": 400, "message": f"Operación no válida: {operation}"}
                )
            
            return ResourceResponse(
                success=True,
                data=result
            )
        
        return ResourceResponse(
            success=False,
            error={"code": 404, "message": f"Recurso API no encontrado: {resource.name}"}
        )
    
    async def _handle_cache_resource(
        self,
        resource: ResourceDefinition,
        request: ResourceRequest
    ) -> ResourceResponse:
        """
        Maneja un recurso de caché
        
        Args:
            resource: Definición del recurso
            request: Solicitud de acceso
            
        Returns:
            ResourceResponse con el resultado
        """
        key = request.parameters.get("key")
        value = request.parameters.get("value")
        ttl = request.parameters.get("ttl", 3600)
        
        if request.action == ResourceAccess.READ:
            result = await self.cache_service.get(key)
            return ResourceResponse(
                success=result is not None,
                data=result
            )
        elif request.action == ResourceAccess.WRITE:
            result = await self.cache_service.set(key, value, ttl)
            return ResourceResponse(
                success=result,
                data={"key": key, "ttl": ttl}
            )
        
        return ResourceResponse(
            success=False,
            error={"code": 400, "message": f"Acción no válida para caché: {request.action}"}
        ) 