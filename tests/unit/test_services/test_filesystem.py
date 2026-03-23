import pytest
from unittest.mock import patch, MagicMock
from app.services.filesystem import FileSystemService
from app.core.exceptions import FileSystemError
import os
from pathlib import Path

class TestFileSystemService:
    """Pruebas unitarias para el servicio de sistema de archivos"""
    
    @pytest.fixture
    def filesystem_service(self, test_data_dir):
        """Fixture para el servicio de sistema de archivos"""
        return FileSystemService(base_dir=test_data_dir)
    
    @pytest.fixture
    def test_file_path(self, test_data_dir):
        """Fixture para la ruta de un archivo de prueba"""
        return test_data_dir / "test_file.txt"
    
    def test_read_file(self, filesystem_service, test_file_path):
        """Prueba la lectura de un archivo"""
        # Crear un archivo de prueba
        test_content = "Test content"
        test_file_path.write_text(test_content)
        
        # Leer el archivo
        content = filesystem_service.read_file(test_file_path)
        
        # Verificar el contenido
        assert content == test_content
        
        # Limpiar
        test_file_path.unlink()
    
    def test_write_file(self, filesystem_service, test_file_path):
        """Prueba la escritura de un archivo"""
        test_content = "Test content"
        
        # Escribir en el archivo
        filesystem_service.write_file(test_file_path, test_content)
        
        # Verificar el contenido
        assert test_file_path.read_text() == test_content
        
        # Limpiar
        test_file_path.unlink()
    
    def test_delete_file(self, filesystem_service, test_file_path):
        """Prueba la eliminación de un archivo"""
        # Crear un archivo de prueba
        test_file_path.write_text("Test content")
        
        # Eliminar el archivo
        filesystem_service.delete_file(test_file_path)
        
        # Verificar que el archivo no existe
        assert not test_file_path.exists()
    
    def test_list_directory(self, filesystem_service, test_data_dir):
        """Prueba la lista de directorios"""
        # Crear archivos de prueba
        (test_data_dir / "file1.txt").write_text("Content 1")
        (test_data_dir / "file2.txt").write_text("Content 2")
        
        # Listar el directorio
        files = filesystem_service.list_directory(test_data_dir)
        
        # Verificar los archivos
        assert len(files) == 2
        assert "file1.txt" in [f.name for f in files]
        assert "file2.txt" in [f.name for f in files]
        
        # Limpiar
        for file in files:
            file.unlink()
    
    def test_file_not_found(self, filesystem_service, test_file_path):
        """Prueba el manejo de archivo no encontrado"""
        with pytest.raises(FileSystemError) as exc_info:
            filesystem_service.read_file(test_file_path)
        
        assert "File not found" in str(exc_info.value)
    
    def test_permission_error(self, filesystem_service, test_file_path):
        """Prueba el manejo de error de permisos"""
        with patch('pathlib.Path.read_text') as mock_read:
            mock_read.side_effect = PermissionError("Permission denied")
            
            with pytest.raises(FileSystemError) as exc_info:
                filesystem_service.read_file(test_file_path)
            
            assert "Permission denied" in str(exc_info.value) 