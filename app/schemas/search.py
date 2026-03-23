from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SearchResult(BaseModel):
    """
    Resultado individual de búsqueda
    """
    title: str = Field(..., description="Título del resultado")
    url: str = Field(..., description="URL del resultado")
    description: str = Field(..., description="Descripción del resultado")
    source: str = Field(..., description="Fuente del resultado")
    published_date: Optional[str] = Field(None, description="Fecha de publicación")
    snippet: Optional[str] = Field(None, description="Fragmento de texto relevante")

class SearchRequest(BaseModel):
    """
    Solicitud de búsqueda
    """
    query: str = Field(..., description="Término de búsqueda")
    num_results: Optional[int] = Field(5, description="Número de resultados a devolver")
    country: Optional[str] = Field("ES", description="País para la búsqueda")
    language: Optional[str] = Field("es", description="Idioma de la búsqueda")
    analyze: Optional[bool] = Field(False, description="Si se debe analizar los resultados con Claude")

class SearchResponse(BaseModel):
    """
    Respuesta de búsqueda
    """
    query: str = Field(..., description="Término de búsqueda original")
    results: List[SearchResult] = Field(..., description="Resultados de la búsqueda")
    total_results: int = Field(..., description="Número total de resultados")
    analysis: Optional[Dict[str, Any]] = Field(None, description="Análisis de los resultados por Claude")

class SearchAnalysis(BaseModel):
    """
    Análisis de resultados de búsqueda
    """
    summary: str = Field(..., description="Resumen general de los resultados")
    key_points: List[str] = Field(..., description="Puntos clave encontrados")
    relevance_score: float = Field(..., description="Puntuación de relevancia (0-1)")
    suggested_queries: List[str] = Field(..., description="Consultas sugeridas relacionadas")

class SearchToolSchema(BaseModel):
    """
    Esquema de la herramienta de búsqueda
    """
    name: str = Field("buscar_en_brave", description="Nombre de la herramienta")
    description: str = Field("Realiza búsquedas web usando Brave Search API", description="Descripción de la herramienta")
    parameters: Dict[str, Any] = Field(
        {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Término de búsqueda"},
                "num_results": {"type": "number", "description": "Número de resultados a devolver"},
                "analyze": {"type": "boolean", "description": "Si se debe analizar los resultados con Claude"}
            },
            "required": ["query"]
        },
        description="Esquema de parámetros de la herramienta"
    ) 