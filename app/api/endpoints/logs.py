from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.core.security import verify_api_key
from app.core.markdown_logger import MarkdownLogger
from app.core.logging import LogManager
from datetime import datetime, timedelta

router = APIRouter(prefix="/logs", tags=["logs"])
markdown_logger = MarkdownLogger()

@router.get("/recent", response_model=List[Dict[str, Any]])
async def get_recent_logs(
    limit: int = 10,
    api_key: str = Depends(verify_api_key)
):
    """
    Obtiene los logs más recientes.
    
    Args:
        limit: Número máximo de logs a devolver
        api_key: API key para autenticación
        
    Returns:
        List[Dict[str, Any]]: Lista de logs recientes
    """
    try:
        # Obtener logs recientes
        logs = markdown_logger.get_recent_operations(limit)
        
        # Registrar operación
        LogManager.log_info(f"Obtenidos {len(logs)} logs recientes")
        
        return logs
        
    except Exception as e:
        LogManager.log_error("logs", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener logs: {str(e)}"
        )

@router.get("/search", response_model=List[Dict[str, Any]])
async def search_logs(
    query: str,
    start_date: datetime = None,
    end_date: datetime = None,
    limit: int = 50,
    api_key: str = Depends(verify_api_key)
):
    """
    Busca logs que coincidan con criterios específicos.
    
    Args:
        query: Término de búsqueda
        start_date: Fecha de inicio para filtrar
        end_date: Fecha de fin para filtrar
        limit: Número máximo de resultados
        api_key: API key para autenticación
        
    Returns:
        List[Dict[str, Any]]: Logs que coinciden con la búsqueda
    """
    try:
        # Obtener todos los logs
        all_logs = markdown_logger.get_recent_operations(1000)  # Obtener más para filtrar
        
        # Filtrar por fecha si se especifica
        if start_date:
            all_logs = [
                log for log in all_logs
                if datetime.fromisoformat(log["timestamp"]) >= start_date
            ]
            
        if end_date:
            all_logs = [
                log for log in all_logs
                if datetime.fromisoformat(log["timestamp"]) <= end_date
            ]
        
        # Filtrar por término de búsqueda
        filtered_logs = [
            log for log in all_logs
            if query.lower() in log["content"].lower()
        ]
        
        # Limitar resultados
        results = filtered_logs[:limit]
        
        # Registrar operación
        LogManager.log_info(
            f"Búsqueda de logs: {len(results)} resultados para '{query}'"
        )
        
        return results
        
    except Exception as e:
        LogManager.log_error("logs", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error al buscar logs: {str(e)}"
        )

@router.get("/stats", response_model=Dict[str, Any])
async def get_log_stats(
    days: int = 7,
    api_key: str = Depends(verify_api_key)
):
    """
    Obtiene estadísticas de los logs.
    
    Args:
        days: Número de días para analizar
        api_key: API key para autenticación
        
    Returns:
        Dict[str, Any]: Estadísticas de los logs
    """
    try:
        # Calcular fechas
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Obtener logs del período
        logs = markdown_logger.get_recent_operations(1000)
        period_logs = [
            log for log in logs
            if start_date <= datetime.fromisoformat(log["timestamp"]) <= end_date
        ]
        
        # Calcular estadísticas
        stats = {
            "total_logs": len(period_logs),
            "by_type": {},
            "by_day": {},
            "errors": 0
        }
        
        for log in period_logs:
            # Contar por tipo
            log_type = log["type"].split(":")[0]
            stats["by_type"][log_type] = stats["by_type"].get(log_type, 0) + 1
            
            # Contar por día
            date = datetime.fromisoformat(log["timestamp"]).date()
            stats["by_day"][str(date)] = stats["by_day"].get(str(date), 0) + 1
            
            # Contar errores
            if "error" in log["content"].lower():
                stats["errors"] += 1
        
        # Registrar operación
        LogManager.log_info(
            f"Estadísticas de logs: {stats['total_logs']} logs en {days} días"
        )
        
        return stats
        
    except Exception as e:
        LogManager.log_error("logs", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener estadísticas: {str(e)}"
        ) 