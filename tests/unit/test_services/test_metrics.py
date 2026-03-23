import os
import json
import pytest
import tempfile
import shutil
from datetime import datetime
from app.services.metrics import MetricsService

class TestMetricsService:
    """Pruebas unitarias para el servicio de métricas"""
    
    @pytest.fixture
    def temp_metrics_dir(self):
        """Fixture para crear un directorio temporal para las métricas"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def metrics_service(self, temp_metrics_dir):
        """Fixture para inicializar el servicio de métricas"""
        return MetricsService(temp_metrics_dir)
    
    def test_setup_metrics_dir(self, temp_metrics_dir):
        """Prueba la creación del directorio de métricas"""
        service = MetricsService(temp_metrics_dir)
        assert os.path.exists(temp_metrics_dir)
    
    def test_record_request(self, metrics_service, temp_metrics_dir):
        """Prueba el registro de solicitudes"""
        # Registrar una solicitud exitosa
        metrics_service.record_request("claude-3-opus", 100, 0.5, True)
        
        # Verificar que se guardaron las métricas
        metrics_file = os.path.join(temp_metrics_dir, "current_metrics.json")
        assert os.path.exists(metrics_file)
        
        with open(metrics_file, "r") as f:
            metrics = json.load(f)
        
        assert metrics["requests"] == 1
        assert metrics["tokens"] == 100
        assert len(metrics["response_times"]) == 1
        assert metrics["response_times"][0] == 0.5
        assert metrics["models_used"]["claude-3-opus"] == 1
        assert metrics["errors"] == 0
        
        # Registrar una solicitud fallida
        metrics_service.record_request("claude-3-opus", 50, 0.3, False)
        
        with open(metrics_file, "r") as f:
            metrics = json.load(f)
        
        assert metrics["requests"] == 2
        assert metrics["tokens"] == 150
        assert len(metrics["response_times"]) == 2
        assert metrics["errors"] == 1
    
    def test_get_metrics(self, metrics_service):
        """Prueba la obtención de métricas"""
        # Registrar algunas solicitudes
        metrics_service.record_request("claude-3-opus", 100, 0.5, True)
        metrics_service.record_request("claude-3-sonnet", 200, 0.7, True)
        
        # Obtener métricas
        metrics = metrics_service.get_metrics()
        
        assert metrics["requests"] == 2
        assert metrics["tokens"] == 300
        assert len(metrics["response_times"]) == 2
        assert "claude-3-opus" in metrics["models_used"]
        assert "claude-3-sonnet" in metrics["models_used"]
    
    def test_get_summary(self, metrics_service):
        """Prueba la obtención del resumen de métricas"""
        # Registrar algunas solicitudes
        metrics_service.record_request("claude-3-opus", 100, 0.5, True)
        metrics_service.record_request("claude-3-opus", 200, 0.7, True)
        
        # Obtener resumen
        summary = metrics_service.get_summary()
        
        assert summary["total_requests"] == 2
        assert summary["total_tokens"] == 300
        assert summary["average_response_time"] == 0.6
        assert "claude-3-opus" in summary["models_used"]
        assert summary["total_errors"] == 0
    
    def test_reset_metrics(self, metrics_service):
        """Prueba el reinicio de métricas"""
        # Registrar algunas solicitudes
        metrics_service.record_request("claude-3-opus", 100, 0.5, True)
        metrics_service.record_request("claude-3-opus", 200, 0.7, True)
        
        # Reiniciar métricas
        metrics_service.reset_metrics()
        
        # Verificar que se reiniciaron
        metrics = metrics_service.get_metrics()
        assert metrics["requests"] == 0
        assert metrics["tokens"] == 0
        assert len(metrics["response_times"]) == 0
        assert len(metrics["models_used"]) == 0
        assert metrics["errors"] == 0
    
    def test_metrics_history(self, metrics_service, temp_metrics_dir):
        """Prueba la creación de historial de métricas"""
        # Registrar una solicitud
        metrics_service.record_request("claude-3-opus", 100, 0.5, True)
        
        # Verificar que se creó un archivo de historial
        history_files = [f for f in os.listdir(temp_metrics_dir) if f.startswith("metrics_")]
        assert len(history_files) == 1
        
        # Verificar el contenido del archivo de historial
        with open(os.path.join(temp_metrics_dir, history_files[0]), "r") as f:
            history = json.load(f)
        
        assert history["requests"] == 1
        assert history["tokens"] == 100
        assert len(history["response_times"]) == 1 