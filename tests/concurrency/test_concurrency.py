"""
Tests de concurrencia para el servidor MCP-Claude.

Este módulo contiene pruebas de concurrencia para evaluar el comportamiento
del sistema bajo condiciones de concurrencia y carga.
"""

import pytest
import asyncio
import time
from typing import List, Dict, Any
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.cache import cache
from app.core.blacklist import blacklist
from app.services.mcp_service import MCPService

client = TestClient(app)
mcp_service = MCPService()

@pytest.mark.concurrency
async def test_concurrent_cache_operations():
    """
    Test de operaciones concurrentes en el sistema de caché.
    """
    num_tasks = 50
    num_operations = 20
    results = []
    
    async def cache_operation(task_id: int):
        for i in range(num_operations):
            key = f"concurrent_key_{task_id}_{i}"
            value = {"data": f"value_{task_id}_{i}"}
            
            # Operación de escritura
            await cache.set(key, value)
            
            # Operación de lectura
            cached_value = await cache.get(key)
            
            # Operación de eliminación
            await cache.delete(key)
            
            results.append((task_id, i, cached_value == value))
    
    tasks = [cache_operation(i) for i in range(num_tasks)]
    await asyncio.gather(*tasks)
    
    # Verificar que todas las operaciones fueron exitosas
    success_rate = sum(1 for _, _, success in results if success) / len(results) * 100
    assert success_rate >= 95, f"Tasa de éxito muy baja en operaciones concurrentes: {success_rate}%"

@pytest.mark.concurrency
async def test_concurrent_blacklist_operations():
    """
    Test de operaciones concurrentes en la lista negra de tokens.
    """
    num_tasks = 50
    num_tokens = 20
    results = []
    
    async def blacklist_operation(task_id: int):
        for i in range(num_tokens):
            token = f"token_{task_id}_{i}"
            
            # Agregar token a la lista negra
            await blacklist.add_to_blacklist(token)
            
            # Verificar si el token está en la lista negra
            is_blacklisted = await blacklist.is_blacklisted(token)
            
            # Eliminar token de la lista negra
            await blacklist.remove_from_blacklist(token)
            
            results.append((task_id, i, is_blacklisted))
    
    tasks = [blacklist_operation(i) for i in range(num_tasks)]
    await asyncio.gather(*tasks)
    
    # Verificar que todas las operaciones fueron exitosas
    success_rate = sum(1 for _, _, success in results if success) / len(results) * 100
    assert success_rate >= 95, f"Tasa de éxito muy baja en operaciones concurrentes: {success_rate}%"

@pytest.mark.concurrency
async def test_concurrent_api_requests():
    """
    Test de solicitudes concurrentes a la API.
    """
    num_tasks = 100
    results = []
    
    async def api_request(task_id: int):
        try:
            response = client.get(
                "/api/v1/mcp/status",
                headers={"X-API-Key": settings.API_KEY}
            )
            results.append((task_id, response.status_code == 200))
        except Exception as e:
            results.append((task_id, False))
    
    tasks = [api_request(i) for i in range(num_tasks)]
    await asyncio.gather(*tasks)
    
    # Verificar que todas las solicitudes fueron exitosas
    success_rate = sum(1 for _, success in results if success) / len(results) * 100
    assert success_rate >= 95, f"Tasa de éxito muy baja en solicitudes concurrentes: {success_rate}%"

@pytest.mark.concurrency
async def test_concurrent_mcp_operations():
    """
    Test de operaciones concurrentes en el servicio MCP.
    """
    num_tasks = 50
    results = []
    
    async def mcp_operation(task_id: int):
        try:
            # Simular una operación MCP
            status = await mcp_service.get_status()
            results.append((task_id, status is not None))
        except Exception as e:
            results.append((task_id, False))
    
    tasks = [mcp_operation(i) for i in range(num_tasks)]
    await asyncio.gather(*tasks)
    
    # Verificar que todas las operaciones fueron exitosas
    success_rate = sum(1 for _, success in results if success) / len(results) * 100
    assert success_rate >= 95, f"Tasa de éxito muy baja en operaciones MCP concurrentes: {success_rate}%"

@pytest.mark.concurrency
async def test_concurrent_plugin_operations():
    """
    Test de operaciones concurrentes con plugins.
    """
    if not settings.PLUGINS_ENABLED:
        pytest.skip("Plugins no están habilitados")
    
    num_tasks = 50
    results = []
    
    async def plugin_operation(task_id: int):
        try:
            # Simular una operación con plugins
            response = client.get(
                "/api/v1/plugins",
                headers={"X-API-Key": settings.API_KEY}
            )
            results.append((task_id, response.status_code == 200))
        except Exception as e:
            results.append((task_id, False))
    
    tasks = [plugin_operation(i) for i in range(num_tasks)]
    await asyncio.gather(*tasks)
    
    # Verificar que todas las operaciones fueron exitosas
    success_rate = sum(1 for _, success in results if success) / len(results) * 100
    assert success_rate >= 95, f"Tasa de éxito muy baja en operaciones de plugins concurrentes: {success_rate}%" 