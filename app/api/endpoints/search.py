from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Optional
# from app.services.brave_search import BraveSearch
from app.services.claude_service import ClaudeService
from app.core.logging import LogManager
from app.core.security import verify_api_key
from app.schemas.search import SearchResponse, SearchAnalysis
from app.core.markdown_logger import MarkdownLogger

router = APIRouter()
# brave_search = BraveSearch()
claude_service = ClaudeService()
markdown_logger = MarkdownLogger()

@router.get("/search", response_model=SearchResponse)
async def search_web(
    query: str = Query(..., description="Término de búsqueda"),
    num_results: int = Query(10, description="Número de resultados a devolver", ge=1, le=50),
    country: str = Query("ES", description="Código de país para resultados"),
    language: str = Query("es", description="Código de idioma para resultados"),
    analyze: bool = Query(False, description="Si se debe analizar los resultados con Claude"),
    api_key: str = Depends(verify_api_key)
):
    """
    Endpoint temporalmente deshabilitado - Brave Search no disponible
    """
    raise HTTPException(
        status_code=501,
        detail="El servicio de búsqueda está temporalmente deshabilitado"
    ) 