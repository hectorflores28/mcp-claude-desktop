from fastapi import APIRouter, Depends, HTTPException
from app.core.security import verify_api_key
from app.core.logging import LogManager
from app.schemas.resources import (
    ResourceRequest,
    ResourceResponse,
    ResourcesResponse,
    ResourceDefinition
)
from app.services.resources_service import ResourcesService

router = APIRouter(prefix="/resources", tags=["resources"])
resources_service = ResourcesService()

@router.get("/", response_model=ResourcesResponse)
async def list_resources(api_key: str = Depends(verify_api_key)):
    """
    Lista todos los recursos disponibles
    """
    try:
        response = await resources_service.list_resources()
        LogManager.log_info(f"Listados {len(response.resources)} recursos")
        return response
    except Exception as e:
        LogManager.log_error("resources", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{name}", response_model=ResourceDefinition)
async def get_resource(name: str, api_key: str = Depends(verify_api_key)):
    """
    Obtiene un recurso por nombre
    """
    try:
        resource = await resources_service.get_resource(name)
        if not resource:
            raise HTTPException(status_code=404, detail=f"Recurso no encontrado: {name}")
        LogManager.log_info(f"Obtenido recurso: {name}")
        return resource
    except HTTPException:
        raise
    except Exception as e:
        LogManager.log_error("resources", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/access", response_model=ResourceResponse)
async def access_resource(request: ResourceRequest, api_key: str = Depends(verify_api_key)):
    """
    Accede a un recurso
    """
    try:
        response = await resources_service.access_resource(request)
        if not response.success:
            raise HTTPException(
                status_code=response.error.get("code", 500),
                detail=response.error.get("message", "Error desconocido")
            )
        LogManager.log_info(f"Accedido recurso: {request.resource}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        LogManager.log_error("resources", str(e))
        raise HTTPException(status_code=500, detail=str(e)) 