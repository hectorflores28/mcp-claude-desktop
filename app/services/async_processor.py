import asyncio
import time
from typing import Dict, List, Any, Optional, Callable, Awaitable
from concurrent.futures import ThreadPoolExecutor
from app.services.metrics import MetricsService
from app.core.logging.claude_logger import ClaudeLogger

class AsyncProcessor:
    """Servicio para procesamiento asíncrono de solicitudes a Claude"""
    
    def __init__(self, max_workers: int = 5, metrics_service: Optional[MetricsService] = None, logger: Optional[ClaudeLogger] = None):
        """
        Inicializa el procesador asíncrono
        
        Args:
            max_workers: Número máximo de trabajadores en el pool
            metrics_service: Servicio de métricas opcional
            logger: Logger opcional
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.metrics_service = metrics_service
        self.logger = logger
        self.tasks: Dict[str, asyncio.Task] = {}
        self.results: Dict[str, Any] = {}
        self.errors: Dict[str, Exception] = {}
    
    async def process_request(self, task_id: str, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> str:
        """
        Procesa una solicitud de forma asíncrona
        
        Args:
            task_id: Identificador único de la tarea
            func: Función asíncrona a ejecutar
            *args: Argumentos posicionales para la función
            **kwargs: Argumentos nombrados para la función
            
        Returns:
            ID de la tarea
        """
        if task_id in self.tasks:
            raise ValueError(f"Ya existe una tarea con ID: {task_id}")
        
        # Crear tarea asíncrona
        task = asyncio.create_task(self._execute_task(task_id, func, *args, **kwargs))
        self.tasks[task_id] = task
        
        return task_id
    
    async def _execute_task(self, task_id: str, func: Callable[..., Awaitable[Any]], *args, **kwargs):
        """
        Ejecuta una tarea y registra su resultado
        
        Args:
            task_id: Identificador de la tarea
            func: Función a ejecutar
            *args: Argumentos posicionales
            **kwargs: Argumentos nombrados
        """
        start_time = time.time()
        success = False
        
        try:
            # Ejecutar función en el pool de hilos
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self.executor, lambda: asyncio.run(func(*args, **kwargs)))
            
            # Registrar resultado
            self.results[task_id] = result
            success = True
            
            # Registrar métricas si está disponible
            if self.metrics_service:
                self.metrics_service.record_request(
                    model=kwargs.get("model", "unknown"),
                    tokens=kwargs.get("tokens", 0),
                    response_time=time.time() - start_time,
                    success=True
                )
            
            # Registrar en logs si está disponible
            if self.logger:
                self.logger.log_app("info", f"Tarea {task_id} completada exitosamente", {
                    "task_id": task_id,
                    "execution_time": time.time() - start_time
                })
                
        except Exception as e:
            # Registrar error
            self.errors[task_id] = e
            success = False
            
            # Registrar métricas si está disponible
            if self.metrics_service:
                self.metrics_service.record_request(
                    model=kwargs.get("model", "unknown"),
                    tokens=kwargs.get("tokens", 0),
                    response_time=time.time() - start_time,
                    success=False
                )
            
            # Registrar en logs si está disponible
            if self.logger:
                self.logger.log_error("TASK_ERROR", str(e), {
                    "task_id": task_id,
                    "execution_time": time.time() - start_time
                })
        
        finally:
            # Limpiar tarea completada
            if task_id in self.tasks:
                del self.tasks[task_id]
    
    async def get_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """
        Obtiene el resultado de una tarea
        
        Args:
            task_id: Identificador de la tarea
            timeout: Tiempo máximo de espera en segundos
            
        Returns:
            Resultado de la tarea
            
        Raises:
            KeyError: Si la tarea no existe
            TimeoutError: Si se excede el tiempo de espera
            Exception: Si la tarea falló
        """
        if task_id in self.errors:
            raise self.errors[task_id]
        
        if task_id not in self.results:
            if task_id in self.tasks:
                try:
                    await asyncio.wait_for(self.tasks[task_id], timeout=timeout)
                except asyncio.TimeoutError:
                    raise TimeoutError(f"Tiempo de espera agotado para la tarea {task_id}")
            else:
                raise KeyError(f"No existe la tarea {task_id}")
        
        return self.results[task_id]
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancela una tarea en ejecución
        
        Args:
            task_id: Identificador de la tarea
            
        Returns:
            True si la tarea fue cancelada, False si no existe
        """
        if task_id in self.tasks:
            self.tasks[task_id].cancel()
            return True
        return False
    
    async def wait_for_all(self, timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Espera a que todas las tareas se completen
        
        Args:
            timeout: Tiempo máximo de espera en segundos
            
        Returns:
            Diccionario con los resultados de todas las tareas
        """
        if not self.tasks:
            return self.results
        
        try:
            await asyncio.wait_for(asyncio.gather(*self.tasks.values(), return_exceptions=True), timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError("Tiempo de espera agotado para algunas tareas")
        
        return self.results
    
    def get_task_status(self, task_id: str) -> str:
        """
        Obtiene el estado de una tarea
        
        Args:
            task_id: Identificador de la tarea
            
        Returns:
            Estado de la tarea: "pending", "completed", "error", "not_found"
        """
        if task_id in self.tasks:
            return "pending"
        elif task_id in self.results:
            return "completed"
        elif task_id in self.errors:
            return "error"
        else:
            return "not_found"
    
    def cleanup(self):
        """Limpia los recursos del procesador"""
        self.executor.shutdown(wait=True)
        self.tasks.clear()
        self.results.clear()
        self.errors.clear() 