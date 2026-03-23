from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.core.security import verify_api_key
from app.core.prompts import PromptTemplates
from app.schemas.mcp import MCPPromptTemplate, MCPPromptTemplatesResponse
from app.core.logging import LogManager

router = APIRouter(prefix="/prompts", tags=["prompts"])

@router.get("/", response_model=MCPPromptTemplatesResponse)
async def list_prompts(
    api_key: str = Depends(verify_api_key)
):
    """
    Lista todas las plantillas de prompts disponibles.
    
    Args:
        api_key: API key para autenticación
        
    Returns:
        MCPPromptTemplatesResponse: Lista de plantillas disponibles
    """
    try:
        # Obtener plantillas
        templates = PromptTemplates.get_all_templates()
        
        # Convertir a formato de respuesta
        prompt_templates = [
            MCPPromptTemplate(
                name=name,
                description=template.get("description", ""),
                template=template.get("template", ""),
                variables=template.get("variables", [])
            )
            for name, template in templates.items()
        ]
        
        # Registrar operación
        LogManager.log_info(
            f"Listado de {len(prompt_templates)} plantillas de prompts"
        )
        
        return MCPPromptTemplatesResponse(templates=prompt_templates)
        
    except Exception as e:
        LogManager.log_error("prompts", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error al listar plantillas: {str(e)}"
        )

@router.get("/{name}", response_model=MCPPromptTemplate)
async def get_prompt(
    name: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Obtiene una plantilla de prompt específica.
    
    Args:
        name: Nombre de la plantilla
        api_key: API key para autenticación
        
    Returns:
        MCPPromptTemplate: Plantilla solicitada
    """
    try:
        # Obtener plantilla
        template = PromptTemplates.get_template(name)
        
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Plantilla no encontrada: {name}"
            )
        
        # Convertir a formato de respuesta
        prompt_template = MCPPromptTemplate(
            name=name,
            description=template.get("description", ""),
            template=template.get("template", ""),
            variables=template.get("variables", [])
        )
        
        # Registrar operación
        LogManager.log_info(f"Obtenida plantilla: {name}")
        
        return prompt_template
        
    except HTTPException:
        raise
    except Exception as e:
        LogManager.log_error("prompts", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener plantilla: {str(e)}"
        )

@router.post("/{name}/format", response_model=Dict[str, str])
async def format_prompt(
    name: str,
    variables: Dict[str, str],
    api_key: str = Depends(verify_api_key)
):
    """
    Formatea una plantilla de prompt con variables específicas.
    
    Args:
        name: Nombre de la plantilla
        variables: Variables para formatear la plantilla
        api_key: API key para autenticación
        
    Returns:
        Dict[str, str]: Prompt formateado
    """
    try:
        # Formatear plantilla
        formatted_prompt = PromptTemplates.format_template(name, variables)
        
        # Registrar operación
        LogManager.log_info(f"Formateada plantilla: {name}")
        
        return {"prompt": formatted_prompt}
        
    except Exception as e:
        LogManager.log_error("prompts", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error al formatear plantilla: {str(e)}"
        ) 