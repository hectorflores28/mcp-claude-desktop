"""
JARVIS - jarvis-memory (Datasets / Conocimiento)
Servidor MCP para guardar, recuperar y buscar datasets de conocimiento.
Funciona como un RAG básico para alimentar contexto a Claude.
"""

from mcp.server.fastmcp import FastMCP
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Cambiar al directorio del script para rutas relativas
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Cargar variables de entorno
load_dotenv()

mcp = FastMCP("jarvis-memory")

# Carpeta donde se guardan los datasets
DATASETS_DIR = os.getenv("DATASETS_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets"))

# Crear carpeta si no existe
os.makedirs(DATASETS_DIR, exist_ok=True)


def ruta_dataset(name: str) -> str:
    """Devuelve la ruta completa de un dataset por nombre."""
    # Sanitizar nombre para uso como nombre de archivo
    safe_name = "".join(c for c in name if c.isalnum() or c in ('-', '_')).lower()
    return os.path.join(DATASETS_DIR, f"{safe_name}.json")


@mcp.tool(name="save_dataset", description="Guarda un dataset de conocimiento con nombre, contenido y tags")
def save_dataset(name: str, content: str, tags: list) -> str:
    """
    Guarda o actualiza un dataset en la carpeta datasets/.
    - name: nombre único del dataset
    - content: texto o datos del conocimiento a guardar
    - tags: lista de etiquetas para facilitar la búsqueda
    """
    try:
        path = ruta_dataset(name)
        # Cargar si ya existe para preservar fecha de creación
        existing = {}
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                existing = json.load(f)

        dataset = {
            "name": name,
            "content": content,
            "tags": tags if isinstance(tags, list) else [tags],
            "created_at": existing.get("created_at", datetime.now().isoformat()),
            "updated_at": datetime.now().isoformat()
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)

        return f"Dataset '{name}' guardado correctamente. Tags: {', '.join(dataset['tags'])}"
    except Exception as e:
        return f"Error al guardar dataset: {str(e)}"


@mcp.tool(name="get_dataset", description="Recupera el contenido completo de un dataset por su nombre")
def get_dataset(name: str) -> str:
    """
    Devuelve el contenido completo del dataset solicitado.
    """
    try:
        path = ruta_dataset(name)
        if not os.path.exists(path):
            return f"Error: Dataset '{name}' no encontrado."

        with open(path, "r", encoding="utf-8") as f:
            dataset = json.load(f)

        return f"[Dataset: {dataset['name']}]\nTags: {', '.join(dataset['tags'])}\n\n{dataset['content']}"
    except Exception as e:
        return f"Error al obtener dataset: {str(e)}"


@mcp.tool(name="search_datasets", description="Busca datasets por nombre o tags")
def search_datasets(query: str) -> str:
    """
    Búsqueda simple: compara la query contra nombre y tags de cada dataset.
    Devuelve los datasets que coincidan.
    """
    try:
        query_lower = query.lower()
        resultados = []

        for filename in os.listdir(DATASETS_DIR):
            if not filename.endswith(".json"):
                continue
            with open(os.path.join(DATASETS_DIR, filename), "r", encoding="utf-8") as f:
                dataset = json.load(f)

            # Buscar en nombre y tags
            coincide = query_lower in dataset["name"].lower() or \
                       any(query_lower in tag.lower() for tag in dataset.get("tags", []))

            if coincide:
                resultados.append(
                    f"• {dataset['name']} | Tags: {', '.join(dataset['tags'])} | Actualizado: {dataset['updated_at'][:10]}"
                )

        if not resultados:
            return f"No se encontraron datasets para '{query}'."

        return f"Resultados para '{query}':\n" + "\n".join(resultados)
    except Exception as e:
        return f"Error al buscar datasets: {str(e)}"


@mcp.tool(name="list_datasets", description="Lista todos los datasets disponibles")
def list_datasets() -> str:
    """
    Devuelve un resumen de todos los datasets guardados.
    """
    try:
        archivos = [f for f in os.listdir(DATASETS_DIR) if f.endswith(".json")]
        if not archivos:
            return "No hay datasets guardados todavía."

        lines = [f"Datasets disponibles ({len(archivos)}):\n"]
        for filename in sorted(archivos):
            with open(os.path.join(DATASETS_DIR, filename), "r", encoding="utf-8") as f:
                dataset = json.load(f)
            lines.append(
                f"• {dataset['name']} | Tags: {', '.join(dataset['tags'])} | Actualizado: {dataset['updated_at'][:10]}"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Error al listar datasets: {str(e)}"


@mcp.tool(name="delete_dataset", description="Elimina un dataset por su nombre")
def delete_dataset(name: str) -> str:
    """
    Elimina permanentemente un dataset de la carpeta datasets/.
    """
    try:
        path = ruta_dataset(name)
        if not os.path.exists(path):
            return f"Error: Dataset '{name}' no encontrado."
        os.remove(path)
        return f"Dataset '{name}' eliminado correctamente."
    except Exception as e:
        return f"Error al eliminar dataset: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
