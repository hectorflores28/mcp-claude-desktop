from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class FileInfo(BaseModel):
    """
    Información de un archivo
    """
    filename: str = Field(..., description="Nombre del archivo")
    path: str = Field(..., description="Ruta del archivo")
    size: int = Field(..., description="Tamaño del archivo en bytes")
    created_at: datetime = Field(..., description="Fecha de creación")
    modified_at: datetime = Field(..., description="Fecha de última modificación")
    content_type: str = Field(..., description="Tipo de contenido")
    extension: str = Field(..., description="Extensión del archivo")

class FileOperation(BaseModel):
    """
    Operación de archivo
    """
    operation: str = Field(..., description="Tipo de operación (create, read, list, delete)")
    filename: Optional[str] = Field(None, description="Nombre del archivo")
    content: Optional[str] = Field(None, description="Contenido del archivo")
    path: Optional[str] = Field(None, description="Ruta del archivo")

class FileResponse(BaseModel):
    """
    Respuesta de operación de archivo
    """
    success: bool = Field(..., description="Si la operación fue exitosa")
    message: str = Field(..., description="Mensaje de la operación")
    file_info: Optional[FileInfo] = Field(None, description="Información del archivo")
    content: Optional[str] = Field(None, description="Contenido del archivo")
    error: Optional[str] = Field(None, description="Mensaje de error si ocurre")

class FileListResponse(BaseModel):
    """
    Respuesta de listado de archivos
    """
    files: List[FileInfo] = Field(..., description="Lista de archivos")
    total: int = Field(..., description="Número total de archivos")
    path: str = Field(..., description="Ruta actual")

class FileSystemToolSchema(BaseModel):
    """
    Esquema de la herramienta de sistema de archivos
    """
    name: str = Field("filesystem", description="Nombre de la herramienta")
    description: str = Field("Operaciones CRUD en el sistema de archivos", description="Descripción de la herramienta")
    parameters: Dict[str, Any] = Field(
        {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "Operación a realizar (create, read, list, delete)",
                    "enum": ["create", "read", "list", "delete"]
                },
                "filename": {"type": "string", "description": "Nombre del archivo"},
                "content": {"type": "string", "description": "Contenido del archivo (para create)"}
            },
            "required": ["operation"]
        },
        description="Esquema de parámetros de la herramienta"
    ) 