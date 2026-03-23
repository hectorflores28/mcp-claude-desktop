import os
import aiofiles
from typing import List, Dict, Optional
from datetime import datetime
from app.core.config import settings
from app.core.logging import LogManager
from app.core.markdown_logger import MarkdownLogger
from app.schemas.filesystem import FileInfo, FileOperation, FileResponse
import magic
import json
from pathlib import Path
import re

class FileSystemService:
    def __init__(self):
        self.data_dir = settings.DATA_DIR
        self.log_dir = settings.LOG_DIR
        self.temp_dir = settings.TEMP_DIR
        self.max_file_size = settings.MAX_FILE_SIZE
        self.allowed_extensions = settings.ALLOWED_EXTENSIONS
        
        # Crear directorios si no existen
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self.logger = MarkdownLogger()
    
    def _get_file_path(self, filename: str) -> str:
        """
        Obtiene la ruta completa del archivo.
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            Ruta completa del archivo
            
        Raises:
            ValueError: Si el nombre del archivo es inválido
        """
        # Validar nombre de archivo
        if not self._is_valid_filename(filename):
            raise ValueError("Nombre de archivo inválido")
            
        # Prevenir directory traversal
        safe_filename = os.path.basename(filename)
        return os.path.join(self.data_dir, safe_filename)
    
    def _is_valid_filename(self, filename: str) -> bool:
        """
        Valida el nombre del archivo.
        
        Args:
            filename: Nombre del archivo a validar
            
        Returns:
            True si el nombre es válido, False en caso contrario
        """
        # Verificar longitud
        if len(filename) > 255:
            return False
            
        # Verificar caracteres permitidos
        if not re.match(r'^[a-zA-Z0-9_.-]+$', filename):
            return False
            
        # Verificar extensión
        if not self._is_allowed_extension(filename):
            return False
            
        return True
    
    def _is_allowed_extension(self, filename: str) -> bool:
        """
        Verifica si la extensión del archivo está permitida.
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            True si la extensión está permitida, False en caso contrario
        """
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    async def save_file(self, content: str, filename: str) -> FileResponse:
        """
        Guarda un archivo en el sistema.
        
        Args:
            content: Contenido del archivo
            filename: Nombre del archivo
            
        Returns:
            FileResponse con información del archivo guardado
            
        Raises:
            ValueError: Si el contenido o nombre del archivo es inválido
            Exception: Si hay un error al guardar el archivo
        """
        try:
            # Validar tamaño
            if len(content.encode('utf-8')) > self.max_file_size:
                raise ValueError(f"Archivo demasiado grande. Máximo: {self.max_file_size} bytes")
            
            # Validar nombre
            if not self._is_valid_filename(filename):
                raise ValueError(f"Nombre de archivo inválido. Extensiones permitidas: {', '.join(self.allowed_extensions)}")
            
            file_path = self._get_file_path(filename)
            
            # Guardar archivo
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            # Obtener información del archivo
            file_info = FileInfo(
                filename=filename,
                path=file_path,
                size=len(content),
                created_at=datetime.now().isoformat(),
                modified_at=datetime.now().isoformat(),
                content_type=magic.from_file(file_path, mime=True),
                extension=filename.rsplit('.', 1)[1].lower()
            )
            
            # Registrar operación
            await self.logger.log_file_operation(
                operation="create",
                filename=filename,
                content=content[:100] + "..." if len(content) > 100 else content
            )
            
            return FileResponse(
                success=True,
                message="Archivo guardado correctamente",
                file_info=file_info
            )
            
        except Exception as e:
            LogManager.log_error("filesystem", str(e))
            return FileResponse(
                success=False,
                message=f"Error al guardar el archivo: {str(e)}",
                error=str(e)
            )
    
    async def read_file(self, filename: str) -> FileResponse:
        """
        Lee un archivo del sistema.
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            FileResponse con el contenido del archivo
            
        Raises:
            FileNotFoundError: Si el archivo no existe
            Exception: Si hay un error al leer el archivo
        """
        try:
            file_path = self._get_file_path(filename)
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Archivo no encontrado: {filename}")
            
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            # Obtener información del archivo
            file_info = FileInfo(
                filename=filename,
                path=file_path,
                size=len(content),
                created_at=datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
                modified_at=datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                content_type=magic.from_file(file_path, mime=True),
                extension=filename.rsplit('.', 1)[1].lower()
            )
            
            # Registrar operación
            await self.logger.log_file_operation(
                operation="read",
                filename=filename,
                content=content[:100] + "..." if len(content) > 100 else content
            )
            
            return FileResponse(
                success=True,
                message="Archivo leído correctamente",
                file_info=file_info,
                content=content
            )
            
        except Exception as e:
            LogManager.log_error("filesystem", str(e))
            return FileResponse(
                success=False,
                message=f"Error al leer el archivo: {str(e)}",
                error=str(e)
            )
    
    async def list_files(self) -> List[FileInfo]:
        """
        Lista todos los archivos en el directorio de datos.
        
        Returns:
            Lista de FileInfo con metadatos de los archivos
        """
        files = []
        for filename in os.listdir(self.data_dir):
            if self._is_allowed_extension(filename):
                file_path = self._get_file_path(filename)
                files.append(FileInfo(
                    filename=filename,
                    path=file_path,
                    size=os.path.getsize(file_path),
                    created_at=datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
                    modified_at=datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                    content_type=magic.from_file(file_path, mime=True),
                    extension=filename.rsplit('.', 1)[1].lower()
                ))
        return files
    
    async def delete_file(self, filename: str) -> FileResponse:
        """
        Elimina un archivo del sistema.
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            FileResponse con información de la operación
            
        Raises:
            FileNotFoundError: Si el archivo no existe
            Exception: Si hay un error al eliminar el archivo
        """
        try:
            file_path = self._get_file_path(filename)
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Archivo no encontrado: {filename}")
            
            # Obtener información del archivo antes de eliminarlo
            file_info = FileInfo(
                filename=filename,
                path=file_path,
                size=os.path.getsize(file_path),
                created_at=datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
                modified_at=datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                content_type=magic.from_file(file_path, mime=True),
                extension=filename.rsplit('.', 1)[1].lower()
            )
            
            # Eliminar archivo
            os.remove(file_path)
            
            # Registrar operación
            await self.logger.log_file_operation(
                operation="delete",
                filename=filename
            )
            
            return FileResponse(
                success=True,
                message="Archivo eliminado correctamente",
                file_info=file_info
            )
            
        except Exception as e:
            LogManager.log_error("filesystem", str(e))
            return FileResponse(
                success=False,
                message=f"Error al eliminar el archivo: {str(e)}",
                error=str(e)
            ) 