from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from app.core.security import verify_api_key
from app.schemas.mcp import ToolDefinition, MCPToolsResponse, MCPRequest, MCPResponse, MCPError
from app.services.brave_search import BraveSearch
from app.services.filesystem_service import FileSystemService
from app.services.claude_service import ClaudeService
from app.core.logging import LogManager

router = APIRouter(prefix="/tools", tags=["tools"])

# Definición de herramientas disponibles
AVAILABLE_TOOLS = [
    ToolDefinition(
        name="buscar_en_brave",
        description="Realiza una búsqueda web utilizando Brave Search API",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Término de búsqueda"
                },
                "num_results": {
                    "type": "integer",
                    "description": "Número de resultados a retornar",
                    "default": 5
                },
                "country": {
                    "type": "string",
                    "description": "Código de país para resultados",
                    "default": "es"
                },
                "language": {
                    "type": "string",
                    "description": "Idioma de los resultados",
                    "default": "es"
                },
                "analyze": {
                    "type": "boolean",
                    "description": "Si se debe analizar los resultados con Claude",
                    "default": False
                }
            },
            "required": ["query"]
        }
    ),
    ToolDefinition(
        name="gestionar_archivo",
        description="Realiza operaciones CRUD en archivos Markdown",
        parameters={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "Tipo de operación (create, read, update, delete)",
                    "enum": ["create", "read", "update", "delete"]
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
            "required": ["operation", "filename"]
        }
    ),
    ToolDefinition(
        name="generar_markdown",
        description="Genera contenido en formato Markdown usando Claude",
        parameters={
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Contenido a formatear"
                },
                "format_type": {
                    "type": "string",
                    "description": "Tipo de formato (article, documentation, etc.)",
                    "default": "article"
                },
                "save": {
                    "type": "boolean",
                    "description": "Si se debe guardar el archivo",
                    "default": False
                },
                "filename": {
                    "type": "string",
                    "description": "Nombre del archivo a guardar"
                }
            },
            "required": ["content"]
        }
    ),
    ToolDefinition(
        name="analizar_texto",
        description="Analiza un texto usando Claude",
        parameters={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Texto a analizar"
                },
                "analysis_type": {
                    "type": "string",
                    "description": "Tipo de análisis (summary, concepts, sentiment)",
                    "enum": ["summary", "concepts", "sentiment"],
                    "default": "summary"
                }
            },
            "required": ["text"]
        }
    )
]

@router.get("/", response_model=MCPToolsResponse)
async def list_tools(
    api_key: str = Depends(verify_api_key)
):
    """
    Lista todas las herramientas MCP disponibles.
    
    Args:
        api_key: API key para autenticación
        
    Returns:
        MCPToolsResponse: Lista de herramientas disponibles
    """
    try:
        # Registrar operación
        LogManager.log_operation(
            "tools",
            "list_tools",
            {"count": len(AVAILABLE_TOOLS)}
        )
        
        return MCPToolsResponse(tools=AVAILABLE_TOOLS)
        
    except Exception as e:
        LogManager.log_error("tools", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error al listar herramientas: {str(e)}"
        )

@router.post("/execute", response_model=MCPResponse)
async def execute_tool(
    request: MCPRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Ejecuta una herramienta MCP específica.
    
    Args:
        request: Solicitud MCP con el método y parámetros
        api_key: API key para autenticación
        
    Returns:
        MCPResponse: Resultado de la ejecución de la herramienta
    """
    try:
        # Validar que el método sea execute_tool
        if request.method != "execute_tool":
            return MCPResponse(
                jsonrpc="2.0",
                error=MCPError(
                    code=-32601,
                    message=f"Método no soportado: {request.method}"
                ),
                id=request.id
            )
        
        # Extraer parámetros
        tool_name = request.params.get("tool_name")
        parameters = request.params.get("parameters", {})
        
        # Registrar operación
        LogManager.log_operation(
            "tools",
            "execute_tool",
            {"tool": tool_name, "parameters": parameters}
        )
        
        # Ejecutar herramienta según su nombre
        result = await _execute_tool_by_name(tool_name, parameters)
        
        return MCPResponse(
            jsonrpc="2.0",
            result=result,
            id=request.id
        )
        
    except Exception as e:
        LogManager.log_error("tools", str(e))
        return MCPResponse(
            jsonrpc="2.0",
            error=MCPError(
                code=-32000,
                message=f"Error al ejecutar herramienta: {str(e)}"
            ),
            id=request.id if hasattr(request, 'id') else None
        )

async def _execute_tool_by_name(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ejecuta una herramienta específica según su nombre.
    
    Args:
        tool_name: Nombre de la herramienta a ejecutar
        parameters: Parámetros para la herramienta
        
    Returns:
        Dict[str, Any]: Resultado de la ejecución
    """
    if tool_name == "buscar_en_brave":
        search_service = BraveSearch()
        return await search_service.search(
            query=parameters.get("query", ""),
            num_results=parameters.get("num_results", 5),
            country=parameters.get("country", "es"),
            language=parameters.get("language", "es"),
            analyze=parameters.get("analyze", False)
        )
        
    elif tool_name == "gestionar_archivo":
        filesystem_service = FileSystemService()
        operation = parameters.get("operation", "")
        filename = parameters.get("filename", "")
        content = parameters.get("content", "")
        
        if operation == "create":
            return await filesystem_service.create_file(filename, content)
        elif operation == "read":
            return await filesystem_service.read_file(filename)
        elif operation == "update":
            return await filesystem_service.update_file(filename, content)
        elif operation == "delete":
            return await filesystem_service.delete_file(filename)
        else:
            raise ValueError(f"Operación no válida: {operation}")
            
    elif tool_name == "generar_markdown":
        claude_service = ClaudeService()
        return await claude_service.generate_markdown(
            content=parameters.get("content", ""),
            format_type=parameters.get("format_type", "article"),
            save=parameters.get("save", False),
            filename=parameters.get("filename", None)
        )
        
    elif tool_name == "analizar_texto":
        claude_service = ClaudeService()
        return await claude_service.analyze_text(
            text=parameters.get("text", ""),
            analysis_type=parameters.get("analysis_type", "summary")
        )
        
    else:
        raise ValueError(f"Herramienta no encontrada: {tool_name}") 