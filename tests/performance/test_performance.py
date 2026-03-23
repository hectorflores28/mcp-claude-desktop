"""
Tests de rendimiento para el servidor MCP-Claude.

Este módulo contiene pruebas de rendimiento para evaluar el comportamiento
del sistema bajo diferentes condiciones de carga.
"""

import pytest
import asyncio
import time
from typing import List, Dict
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.cache import cache
from app.core.blacklist import blacklist

client = TestClient(app)

@pytest.mark.performance
async def test_concurrent_requests():
    """
    Test de rendimiento para solicitudes concurrentes.
    """
    num_requests = 100
    start_time = time.time()
    
    async def make_request():
        response = client.get("/health")
        return response.status_code == 200
    
    tasks = [make_request() for _ in range(num_requests)]
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    total_time = end_time - start_time
    success_rate = sum(results) / len(results) * 100
    
    assert success_rate >= 95, f"Tasa de éxito muy baja: {success_rate}%"
    assert total_time < 5, f"Tiempo de respuesta muy alto: {total_time}s"

@pytest.mark.performance
async def test_cache_performance():
    """
    Test de rendimiento del sistema de caché.
    """
    num_operations = 1000
    start_time = time.time()
    
    # Operaciones de escritura
    for i in range(num_operations):
        await cache.set(f"test_key_{i}", {"data": f"value_{i}"})
    
    # Operaciones de lectura
    for i in range(num_operations):
        await cache.get(f"test_key_{i}")
    
    end_time = time.time()
    total_time = end_time - start_time
    ops_per_second = (num_operations * 2) / total_time
    
    assert ops_per_second >= 1000, f"Rendimiento de caché muy bajo: {ops_per_second} ops/s"

@pytest.mark.performance
async def test_blacklist_performance():
    """
    Test de rendimiento de la lista negra de tokens.
    """
    num_tokens = 1000
    start_time = time.time()
    
    # Agregar tokens
    for i in range(num_tokens):
        await blacklist.add_to_blacklist(f"token_{i}")
    
    # Verificar tokens
    for i in range(num_tokens):
        await blacklist.is_blacklisted(f"token_{i}")
    
    end_time = time.time()
    total_time = end_time - start_time
    ops_per_second = (num_tokens * 2) / total_time
    
    assert ops_per_second >= 1000, f"Rendimiento de blacklist muy bajo: {ops_per_second} ops/s"

@pytest.mark.performance
async def test_api_endpoints_performance():
    """
    Test de rendimiento de los endpoints de la API.
    """
    endpoints = [
        "/health",
        "/status",
        "/api/v1/mcp/status"
    ]
    
    num_requests = 100
    results: Dict[str, List[float]] = {}
    
    for endpoint in endpoints:
        times = []
        for _ in range(num_requests):
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()
            
            assert response.status_code == 200
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        results[endpoint] = times
        
        assert avg_time < 0.1, f"Tiempo de respuesta muy alto para {endpoint}: {avg_time}s"
    
    return results 