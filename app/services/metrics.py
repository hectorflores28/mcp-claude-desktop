import time
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class MetricsService:
    """Servicio para recopilar y gestionar métricas de la aplicación"""
    
    def __init__(self, metrics_dir: str = "data/metrics"):
        """
        Inicializa el servicio de métricas
        
        Args:
            metrics_dir: Directorio para almacenar las métricas
        """
        self.metrics_dir = metrics_dir
        self.setup_metrics_dir()
        self.current_metrics = {
            "requests": 0,
            "tokens": 0,
            "errors": 0,
            "response_times": [],
            "models_used": {},
            "last_updated": datetime.now().isoformat()
        }
    
    def setup_metrics_dir(self):
        """Crea el directorio de métricas si no existe"""
        os.makedirs(self.metrics_dir, exist_ok=True)
    
    def record_request(self, model: str, tokens: int, response_time: float, success: bool = True):
        """
        Registra una solicitud a la API
        
        Args:
            model: Modelo utilizado
            tokens: Número de tokens utilizados
            response_time: Tiempo de respuesta en segundos
            success: Si la solicitud fue exitosa
        """
        self.current_metrics["requests"] += 1
        self.current_metrics["tokens"] += tokens
        self.current_metrics["response_times"].append(response_time)
        
        if not success:
            self.current_metrics["errors"] += 1
        
        if model in self.current_metrics["models_used"]:
            self.current_metrics["models_used"][model] += 1
        else:
            self.current_metrics["models_used"][model] = 1
        
        self.current_metrics["last_updated"] = datetime.now().isoformat()
        self._save_metrics()
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Obtiene las métricas actuales
        
        Returns:
            Dict con las métricas actuales
        """
        return self.current_metrics
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen de las métricas
        
        Returns:
            Dict con el resumen de métricas
        """
        response_times = self.current_metrics["response_times"]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "total_requests": self.current_metrics["requests"],
            "total_tokens": self.current_metrics["tokens"],
            "total_errors": self.current_metrics["errors"],
            "average_response_time": avg_response_time,
            "models_used": self.current_metrics["models_used"],
            "last_updated": self.current_metrics["last_updated"]
        }
    
    def reset_metrics(self):
        """Reinicia las métricas actuales"""
        self.current_metrics = {
            "requests": 0,
            "tokens": 0,
            "errors": 0,
            "response_times": [],
            "models_used": {},
            "last_updated": datetime.now().isoformat()
        }
        self._save_metrics()
    
    def _save_metrics(self):
        """Guarda las métricas actuales en un archivo"""
        metrics_file = os.path.join(self.metrics_dir, "current_metrics.json")
        with open(metrics_file, "w") as f:
            json.dump(self.current_metrics, f, indent=2)
        
        # Guardar un historial de métricas
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        history_file = os.path.join(self.metrics_dir, f"metrics_{timestamp}.json")
        with open(history_file, "w") as f:
            json.dump(self.current_metrics, f, indent=2) 