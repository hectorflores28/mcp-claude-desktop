import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.core.config import settings

class MarkdownLogger:
    """Clase para registrar operaciones en formato Markdown."""
    
    def __init__(self):
        self.log_dir = settings.LOG_DIR
        self.log_file = os.path.join(self.log_dir, "log.md")
        
        # Crear el directorio si no existe
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Crear el archivo de log si no existe
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.write("# Registro de Operaciones MCP\n\n")
                f.write("Este archivo registra todas las operaciones realizadas en el servidor MCP.\n\n")
                f.write("## Índice\n\n")
                f.write("- [Operaciones de Búsqueda](#operaciones-de-búsqueda)\n")
                f.write("- [Operaciones de Archivos](#operaciones-de-archivos)\n")
                f.write("- [Operaciones de Claude](#operaciones-de-claude)\n\n")
                f.write("## Operaciones de Búsqueda\n\n")
                f.write("## Operaciones de Archivos\n\n")
                f.write("## Operaciones de Claude\n\n")
    
    def log_search(self, query: str, num_results: int, results: List[Dict[str, Any]]) -> None:
        """
        Registra una operación de búsqueda.
        
        Args:
            query: Término de búsqueda
            num_results: Número de resultados
            results: Resultados de la búsqueda
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"### Búsqueda: {query} ({timestamp})\n\n")
            f.write(f"- **Consulta**: {query}\n")
            f.write(f"- **Resultados**: {num_results}\n\n")
            
            for i, result in enumerate(results, 1):
                f.write(f"{i}. [{result.get('title', 'Sin título')}]({result.get('url', '#')})\n")
                f.write(f"   - {result.get('description', 'Sin descripción')}\n\n")
            
            f.write("---\n\n")
    
    def log_file_operation(self, operation: str, filename: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Registra una operación de archivo.
        
        Args:
            operation: Tipo de operación (create, read, update, delete)
            filename: Nombre del archivo
            details: Detalles adicionales
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"### {operation.capitalize()}: {filename} ({timestamp})\n\n")
            
            if details:
                for key, value in details.items():
                    f.write(f"- **{key}**: {value}\n")
            
            f.write("---\n\n")
    
    def log_claude_operation(self, operation: str, details: Dict[str, Any]) -> None:
        """
        Registra una operación de Claude.
        
        Args:
            operation: Tipo de operación
            details: Detalles de la operación
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"### Claude: {operation} ({timestamp})\n\n")
            
            for key, value in details.items():
                if key == "prompt" and isinstance(value, str) and len(value) > 100:
                    f.write(f"- **{key}**: {value[:100]}...\n")
                elif key == "response" and isinstance(value, str) and len(value) > 100:
                    f.write(f"- **{key}**: {value[:100]}...\n")
                else:
                    f.write(f"- **{key}**: {value}\n")
            
            f.write("---\n\n")
    
    def get_recent_operations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene las operaciones más recientes.
        
        Args:
            limit: Número máximo de operaciones a devolver
            
        Returns:
            Lista de operaciones recientes
        """
        operations = []
        
        with open(self.log_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Extraer las secciones de operaciones
        sections = content.split("---")
        
        for section in sections:
            if not section.strip():
                continue
                
            lines = section.strip().split("\n")
            if not lines:
                continue
                
            header = lines[0].strip()
            if not header.startswith("###"):
                continue
                
            # Extraer información de la cabecera
            header_parts = header.replace("###", "").strip().split("(")
            operation_type = header_parts[0].strip()
            timestamp = header_parts[1].replace(")", "").strip() if len(header_parts) > 1 else ""
            
            operations.append({
                "type": operation_type,
                "timestamp": timestamp,
                "content": section.strip()
            })
            
            if len(operations) >= limit:
                break
        
        return operations 