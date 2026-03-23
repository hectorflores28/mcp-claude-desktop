import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock
from app.services.async_processor import AsyncProcessor
from app.services.metrics import MetricsService
from app.core.logging.claude_logger import ClaudeLogger

@pytest.fixture
def metrics_service():
    return Mock(spec=MetricsService)

@pytest.fixture
def logger():
    return Mock(spec=ClaudeLogger)

@pytest.fixture
def processor(metrics_service, logger):
    return AsyncProcessor(max_workers=2, metrics_service=metrics_service, logger=logger)

@pytest.mark.asyncio
async def test_process_request_success(processor):
    """Prueba el procesamiento exitoso de una solicitud"""
    async def mock_func(*args, **kwargs):
        await asyncio.sleep(0.1)
        return {"result": "success"}
    
    task_id = "test_task"
    result = await processor.process_request(task_id, mock_func)
    assert result == task_id
    
    # Esperar resultado
    result = await processor.get_result(task_id)
    assert result == {"result": "success"}
    
    # Verificar estado
    assert processor.get_task_status(task_id) == "completed"

@pytest.mark.asyncio
async def test_process_request_error(processor, metrics_service, logger):
    """Prueba el procesamiento de una solicitud con error"""
    async def mock_func(*args, **kwargs):
        await asyncio.sleep(0.1)
        raise ValueError("Test error")
    
    task_id = "test_error"
    await processor.process_request(task_id, mock_func)
    
    # Verificar que se lanza la excepción
    with pytest.raises(ValueError, match="Test error"):
        await processor.get_result(task_id)
    
    # Verificar estado
    assert processor.get_task_status(task_id) == "error"
    
    # Verificar métricas y logs
    metrics_service.record_request.assert_called_with(
        model="unknown",
        tokens=0,
        response_time=pytest.approx(0.1, abs=0.1),
        success=False
    )
    logger.log_error.assert_called_once()

@pytest.mark.asyncio
async def test_cancel_task(processor):
    """Prueba la cancelación de una tarea"""
    async def mock_func(*args, **kwargs):
        await asyncio.sleep(1)
        return {"result": "success"}
    
    task_id = "test_cancel"
    await processor.process_request(task_id, mock_func)
    
    # Cancelar tarea
    assert processor.cancel_task(task_id) == True
    
    # Verificar estado
    assert processor.get_task_status(task_id) == "not_found"

@pytest.mark.asyncio
async def test_wait_for_all(processor):
    """Prueba esperar a que todas las tareas se completen"""
    async def mock_func(result, delay=0.1):
        await asyncio.sleep(delay)
        return {"result": result}
    
    # Crear múltiples tareas
    task_ids = []
    for i in range(3):
        task_id = f"task_{i}"
        await processor.process_request(task_id, mock_func, f"result_{i}")
        task_ids.append(task_id)
    
    # Esperar a que todas se completen
    results = await processor.wait_for_all()
    
    # Verificar resultados
    for i, task_id in enumerate(task_ids):
        assert results[task_id]["result"] == f"result_{i}"
        assert processor.get_task_status(task_id) == "completed"

@pytest.mark.asyncio
async def test_wait_for_all_timeout(processor):
    """Prueba el timeout al esperar todas las tareas"""
    async def mock_func():
        await asyncio.sleep(1)
        return {"result": "success"}
    
    # Crear tarea larga
    await processor.process_request("long_task", mock_func)
    
    # Verificar timeout
    with pytest.raises(TimeoutError):
        await processor.wait_for_all(timeout=0.1)

def test_cleanup(processor):
    """Prueba la limpieza de recursos"""
    processor.cleanup()
    
    # Verificar que las colecciones están vacías
    assert len(processor.tasks) == 0
    assert len(processor.results) == 0
    assert len(processor.errors) == 0 