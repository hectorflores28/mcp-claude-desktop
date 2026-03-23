from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
import time
import logging

from app.schemas.mcp import (
    MCPRequest, MCPResponse, MCPError, MCPStatus, 
    MCPOperation, MCPExecuteRequest, MCPExecuteResponse
)
from app.services.mcp_service import MCPService
from app.core.logging import LogManager

router = APIRouter(prefix="/mcp", tags=["mcp"])
mcp_service = MCPService()
logger = logging.getLogger(__name__)

@router.get("/status", response_model=MCPStatus)
async def mcp_status():
    """
    Obtiene el estado del protocolo MCP
    """
    try:
        LogManager.log_info("Obteniendo estado del protocolo MCP")
        status = await mcp_service.get_status()
        LogManager.log_info(f"Estado del protocolo MCP obtenido: {status}")
        return status
    except Exception as e:
        LogManager.log_error("mcp", f"Error al obtener estado: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute", response_model=MCPResponse)
async def execute_mcp(request: MCPRequest):
    """
    Ejecuta una solicitud MCP
    """
    try:
        LogManager.log_info(f"Ejecutando solicitud MCP: {request}")
        start_time = time.time()
        response = await mcp_service.process_request(request)
        execution_time = time.time() - start_time
        response.execution_time = execution_time
        LogManager.log_info(f"Respuesta MCP: {response}")
        return response
    except Exception as e:
        LogManager.log_error("mcp", f"Error al ejecutar solicitud: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/operations", response_model=List[MCPOperation])
async def get_recent_operations(limit: int = 10):
    """
    Obtiene las operaciones más recientes
    """
    try:
        LogManager.log_info(f"Obteniendo {limit} operaciones recientes")
        operations = await mcp_service.get_recent_operations(limit)
        LogManager.log_info(f"Se obtuvieron {len(operations)} operaciones")
        return operations
    except Exception as e:
        LogManager.log_error("mcp", f"Error al obtener operaciones: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 