from typing import Dict, Optional, List
from datetime import datetime
import time
from prometheus_client import Counter, Histogram, Gauge
from app.core.logging import LogManager
from dataclasses import dataclass, field
import json
import threading
import asyncio
from app.core.cache import get_cache

@dataclass
class APIMetric:
    """Métrica individual de API"""
    endpoint: str
    method: str
    status_code: int
    response_time: float
    timestamp: datetime = field(default_factory=datetime.now)
    tokens_used: Optional[int] = None
    error_type: Optional[str] = None

@dataclass
class PerformanceMetric:
    """Métrica de rendimiento del sistema"""
    cpu_usage: float
    memory_usage: float
    active_connections: int
    timestamp: datetime = field(default_factory=datetime.now)

class MetricsCollector:
    """Recolector de métricas para MCP-Claude"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._cache = get_cache()
            self._batch_size = 100
            self._flush_interval = 60  # 1 minuto
            self._last_flush = time.time()
            self._flush_lock = asyncio.Lock()
            
            # Métricas Prometheus
            self.api_requests = Counter(
                'mcp_api_requests_total',
                'Total de solicitudes API',
                ['endpoint', 'method', 'status_code']
            )
            self.api_latency = Histogram(
                'mcp_api_latency_seconds',
                'Latencia de solicitudes API',
                ['endpoint', 'method']
            )
            self.active_connections = Gauge(
                'mcp_active_connections',
                'Conexiones activas'
            )
            self.cpu_usage = Gauge(
                'mcp_cpu_usage_percent',
                'Uso de CPU'
            )
            self.memory_usage = Gauge(
                'mcp_memory_usage_percent',
                'Uso de memoria'
            )
            
            # Buffers para métricas
            self._api_metrics_buffer: List[APIMetric] = []
            self._performance_metrics_buffer: List[PerformanceMetric] = []
            
            self._initialized = True
    
    async def record_api_call(self, metric: APIMetric) -> None:
        """
        Registra una métrica de API
        
        Args:
            metric: Métrica a registrar
        """
        try:
            # Actualizar Prometheus
            self.api_requests.labels(
                endpoint=metric.endpoint,
                method=metric.method,
                status_code=metric.status_code
            ).inc()
            
            self.api_latency.labels(
                endpoint=metric.endpoint,
                method=metric.method
            ).observe(metric.response_time)
            
            # Añadir a buffer
            self._api_metrics_buffer.append(metric)
            
            # Flush si es necesario
            await self._flush_if_needed()
        except Exception as e:
            LogManager.log_error("metrics", f"Error al registrar métrica de API: {str(e)}")
    
    async def record_performance(self, metric: PerformanceMetric) -> None:
        """
        Registra una métrica de rendimiento
        
        Args:
            metric: Métrica a registrar
        """
        try:
            # Actualizar Prometheus
            self.active_connections.set(metric.active_connections)
            self.cpu_usage.set(metric.cpu_usage)
            self.memory_usage.set(metric.memory_usage)
            
            # Añadir a buffer
            self._performance_metrics_buffer.append(metric)
            
            # Flush si es necesario
            await self._flush_if_needed()
        except Exception as e:
            LogManager.log_error("metrics", f"Error al registrar métrica de rendimiento: {str(e)}")
    
    async def _flush_if_needed(self) -> None:
        """
        Flush los buffers si es necesario
        """
        current_time = time.time()
        if (current_time - self._last_flush >= self._flush_interval or
            len(self._api_metrics_buffer) >= self._batch_size or
            len(self._performance_metrics_buffer) >= self._batch_size):
            await self._flush()
    
    async def _flush(self) -> None:
        """
        Flush los buffers a Redis
        """
        async with self._flush_lock:
            try:
                # Preparar datos para API metrics
                if self._api_metrics_buffer:
                    api_data = [
                        {
                            "endpoint": m.endpoint,
                            "method": m.method,
                            "status_code": m.status_code,
                            "response_time": m.response_time,
                            "timestamp": m.timestamp.isoformat(),
                            "tokens_used": m.tokens_used,
                            "error_type": m.error_type
                        }
                        for m in self._api_metrics_buffer
                    ]
                    
                    # Almacenar en Redis
                    await self._cache.set_many({
                        f"metrics:api:{i}": data
                        for i, data in enumerate(api_data)
                    }, ttl=86400)  # 24 horas
                    
                    # Limpiar buffer
                    self._api_metrics_buffer.clear()
                
                # Preparar datos para performance metrics
                if self._performance_metrics_buffer:
                    perf_data = [
                        {
                            "cpu_usage": m.cpu_usage,
                            "memory_usage": m.memory_usage,
                            "active_connections": m.active_connections,
                            "timestamp": m.timestamp.isoformat()
                        }
                        for m in self._performance_metrics_buffer
                    ]
                    
                    # Almacenar en Redis
                    await self._cache.set_many({
                        f"metrics:perf:{i}": data
                        for i, data in enumerate(perf_data)
                    }, ttl=86400)  # 24 horas
                    
                    # Limpiar buffer
                    self._performance_metrics_buffer.clear()
                
                self._last_flush = time.time()
                LogManager.log_info("metrics", "Métricas almacenadas correctamente")
            except Exception as e:
                LogManager.log_error("metrics", f"Error al almacenar métricas: {str(e)}")
    
    async def get_api_metrics(self, limit: int = 100) -> List[Dict]:
        """
        Obtiene métricas de API
        
        Args:
            limit: Límite de métricas a obtener
            
        Returns:
            Lista de métricas
        """
        try:
            # Obtener claves
            keys = [f"metrics:api:{i}" for i in range(limit)]
            
            # Obtener valores
            values = await self._cache.get_many(keys)
            
            # Procesar resultados
            metrics = []
            for value in values.values():
                if value:
                    metrics.append(value)
            
            return sorted(
                metrics,
                key=lambda x: x["timestamp"],
                reverse=True
            )
        except Exception as e:
            LogManager.log_error("metrics", f"Error al obtener métricas de API: {str(e)}")
            return []
    
    async def get_performance_metrics(self, limit: int = 100) -> List[Dict]:
        """
        Obtiene métricas de rendimiento
        
        Args:
            limit: Límite de métricas a obtener
            
        Returns:
            Lista de métricas
        """
        try:
            # Obtener claves
            keys = [f"metrics:perf:{i}" for i in range(limit)]
            
            # Obtener valores
            values = await self._cache.get_many(keys)
            
            # Procesar resultados
            metrics = []
            for value in values.values():
                if value:
                    metrics.append(value)
            
            return sorted(
                metrics,
                key=lambda x: x["timestamp"],
                reverse=True
            )
        except Exception as e:
            LogManager.log_error("metrics", f"Error al obtener métricas de rendimiento: {str(e)}")
            return []

# Instancia global de métricas
metrics = MetricsCollector()

class MetricsMiddleware:
    """Middleware para recolección automática de métricas"""
    
    def __init__(self, app):
        self.app = app
        self.collector = MetricsCollector()
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        
        start_time = time.time()
        path = scope["path"]
        method = scope["method"]
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code = message["status"]
                response_time = time.time() - start_time
                
                metric = APIMetric(
                    endpoint=path,
                    method=method,
                    status_code=status_code,
                    response_time=response_time
                )
                
                self.collector.record_api_call(metric)
                LogManager.log_info(
                    "API_METRIC",
                    f"Endpoint: {path}, Method: {method}, "
                    f"Status: {status_code}, Time: {response_time:.3f}s"
                )
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)

def record_performance_metric():
    """Decorador para registrar métricas de rendimiento de funciones"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            metric = PerformanceMetric(
                cpu_usage=0.0,  # Esto debería ser implementado con psutil
                memory_usage=0.0,  # Esto debería ser implementado con psutil
                active_connections=0  # Esto debería ser implementado con el contador de conexiones
            )
            
            MetricsCollector().record_performance(metric)
            return result
        
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            metric = PerformanceMetric(
                cpu_usage=0.0,  # Esto debería ser implementado con psutil
                memory_usage=0.0,  # Esto debería ser implementado con psutil
                active_connections=0  # Esto debería ser implementado con el contador de conexiones
            )
            
            MetricsCollector().record_performance(metric)
            return result
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

class ClaudeMetrics:
    """Sistema de métricas para Claude API"""
    
    def __init__(self):
        self.logger = LogManager.get_logger("claude_metrics")
        
        # Contadores
        self.requests_total = Counter(
            'claude_requests_total',
            'Total de solicitudes a Claude API',
            ['endpoint', 'model']
        )
        
        self.tokens_total = Counter(
            'claude_tokens_total',
            'Total de tokens procesados',
            ['type', 'model']
        )
        
        # Histogramas
        self.request_duration = Histogram(
            'claude_request_duration_seconds',
            'Duración de las solicitudes a Claude API',
            ['endpoint', 'model'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        )
        
        # Gauges
        self.active_requests = Gauge(
            'claude_active_requests',
            'Número de solicitudes activas',
            ['model']
        )
        
        self.rate_limit_remaining = Gauge(
            'claude_rate_limit_remaining',
            'Solicitudes restantes en el límite de tasa',
            ['model']
        )
    
    def track_request_start(self, endpoint: str, model: str) -> None:
        """Registra el inicio de una solicitud"""
        self.active_requests.labels(model=model).inc()
        self.requests_total.labels(endpoint=endpoint, model=model).inc()
        self.logger.debug(f"Iniciando solicitud a {endpoint} con modelo {model}")
    
    def track_request_end(self, endpoint: str, model: str, duration: float) -> None:
        """Registra el fin de una solicitud"""
        self.active_requests.labels(model=model).dec()
        self.request_duration.labels(endpoint=endpoint, model=model).observe(duration)
        self.logger.debug(f"Finalizando solicitud a {endpoint} con modelo {model} en {duration:.2f}s")
    
    def track_tokens(self, count: int, token_type: str, model: str) -> None:
        """Registra el uso de tokens"""
        self.tokens_total.labels(type=token_type, model=model).inc(count)
        self.logger.debug(f"Tokens {token_type} utilizados: {count} para modelo {model}")
    
    def update_rate_limit(self, remaining: int, model: str) -> None:
        """Actualiza el contador de límite de tasa"""
        self.rate_limit_remaining.labels(model=model).set(remaining)
        self.logger.debug(f"Límite de tasa restante para {model}: {remaining}")
    
    def track_error(self, endpoint: str, model: str, error_type: str) -> None:
        """Registra errores en las solicitudes"""
        self.requests_total.labels(
            endpoint=f"{endpoint}_error_{error_type}",
            model=model
        ).inc()
        self.logger.warning(f"Error en solicitud a {endpoint} con modelo {model}: {error_type}")

# Singleton instance
claude_metrics = ClaudeMetrics() 