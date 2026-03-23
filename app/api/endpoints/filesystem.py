from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.core.security import verify_api_key
from app.services.filesystem_service import FileSystemService
from app.schemas.filesystem import (
    FileOperation,
    FileResponse,
    FileListResponse
)
from app.core.logging import LogManager

router = APIRouter(prefix="/filesystem", tags=["filesystem"])

@router.post("/", response_model=FileResponse)
async def create_file(
    operation: FileOperation,
    api_key: str = Depends(verify_api_key)
):
    """
    Crea un nuevo archivo en el sistema.
    
    Args:
        operation: Detalles de la operación de archivo
        api_key: API key para autenticación
        
    Returns:
        FileResponse: Resultado de la operación
    """
    try:
        service = FileSystemService()
        response = await service.create_file(
            filename=operation.filename,
            content=operation.content
        )
        return response
    except Exception as e:
        LogManager.log_error("filesystem", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear archivo: {str(e)}"
        )

@router.get("/{filename}", response_model=FileResponse)
async def read_file(
    filename: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Lee un archivo existente.
    
    Args:
        filename: Nombre del archivo a leer
        api_key: API key para autenticación
        
    Returns:
        FileResponse: Contenido del archivo
    """
    try:
        service = FileSystemService()
        response = await service.read_file(filename)
        return response
    except Exception as e:
        LogManager.log_error("filesystem", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error al leer archivo: {str(e)}"
        )

@router.get("/", response_model=FileListResponse)
async def list_files(
    api_key: str = Depends(verify_api_key)
):
    """
    Lista todos los archivos disponibles.
    
    Args:
        api_key: API key para autenticación
        
    Returns:
        FileListResponse: Lista de archivos
    """
    try:
        service = FileSystemService()
        response = await service.list_files()
        return response
    except Exception as e:
        LogManager.log_error("filesystem", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error al listar archivos: {str(e)}"
        )

@router.put("/{filename}", response_model=FileResponse)
async def update_file(
    filename: str,
    operation: FileOperation,
    api_key: str = Depends(verify_api_key)
):
    """
    Actualiza un archivo existente.
    
    Args:
        filename: Nombre del archivo a actualizar
        operation: Detalles de la operación
        api_key: API key para autenticación
        
    Returns:
        FileResponse: Resultado de la operación
    """
    try:
        service = FileSystemService()
        response = await service.update_file(
            filename=filename,
            content=operation.content
        )
        return response
    except Exception as e:
        LogManager.log_error("filesystem", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar archivo: {str(e)}"
        )

@router.delete("/{filename}", response_model=FileResponse)
async def delete_file(
    filename: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Elimina un archivo existente.
    
    Args:
        filename: Nombre del archivo a eliminar
        api_key: API key para autenticación
        
    Returns:
        FileResponse: Resultado de la operación
    """
    try:
        service = FileSystemService()
        response = await service.delete_file(filename)
        return response
    except Exception as e:
        LogManager.log_error("filesystem", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar archivo: {str(e)}"
        ) 