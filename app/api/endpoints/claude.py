from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional
import time
from app.core.config import settings
from app.core.logging import LogManager
from app.core.security import get_current_user
from app.core.metrics import MetricsCollector
from app.services.claude_service import get_claude_service
from app.schemas.claude import ClaudeRequest, ClaudeResponse, ClaudeAnalysis

router = APIRouter(prefix="/claude", tags=["claude"])
logger = LogManager.get_logger("claude_endpoints")
metrics = MetricsCollector()

@router.get("/status")
async def claude_status() -> Dict[str, Any]:
    """
    Verifica el estado del servicio Claude
    """
    start_time = time.time()
    
    try:
        # Obtener estado del servicio
        service = get_claude_service()
        status = await service.get_status()
        
        # Registrar métricas
        await metrics.record_api_call(
            endpoint="claude_status",
            method="GET",
            status_code=200,
            response_time=time.time() - start_time
        )
        
        return status
        
    except Exception as e:
        # Registrar error en métricas
        await metrics.record_api_call(
            endpoint="claude_status",
            method="GET",
            status_code=500,
            response_time=time.time() - start_time
        )
        
        logger.error(f"Error al obtener estado de Claude: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener estado de Claude"
        )

@router.post("/mcp_completion", response_model=ClaudeResponse)
async def mcp_completion(
    request: ClaudeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> ClaudeResponse:
    """
    Procesa una solicitud de completado usando Claude API
    
    Args:
        request: Solicitud de completado
        current_user: Usuario actual autenticado
        
    Returns:
        ClaudeResponse con la respuesta generada
    """
    start_time = time.time()
    
    try:
        # Verificar API key
        if not current_user.get("api_key"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key no proporcionada"
            )
        
        # Procesar solicitud
        service = get_claude_service()
        response = await service.mcp_completion(request)
        
        # Registrar métricas
        await metrics.record_api_call(
            endpoint="mcp_completion",
            method="POST",
            status_code=200,
            response_time=time.time() - start_time
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        # Registrar error en métricas
        await metrics.record_api_call(
            endpoint="mcp_completion",
            method="POST",
            status_code=500,
            response_time=time.time() - start_time
        )
        
        logger.error(f"Error al procesar solicitud de completado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al procesar solicitud de completado"
        )

@router.post("/analyze", response_model=ClaudeAnalysis)
async def analyze_text(
    text: str,
    analysis_type: str = "general",
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> ClaudeAnalysis:
    """
    Analiza un texto usando Claude API
    
    Args:
        text: Texto a analizar
        analysis_type: Tipo de análisis a realizar
        current_user: Usuario actual autenticado
        
    Returns:
        ClaudeAnalysis con el resultado del análisis
    """
    start_time = time.time()
    
    try:
        # Verificar API key
        if not current_user.get("api_key"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key no proporcionada"
            )
        
        # Analizar texto
        service = get_claude_service()
        analysis = await service.analyze_text(text, analysis_type)
        
        # Registrar métricas
        await metrics.record_api_call(
            endpoint="analyze_text",
            method="POST",
            status_code=200,
            response_time=time.time() - start_time
        )
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        # Registrar error en métricas
        await metrics.record_api_call(
            endpoint="analyze_text",
            method="POST",
            status_code=500,
            response_time=time.time() - start_time
        )
        
        logger.error(f"Error al analizar texto: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al analizar texto"
        ) 