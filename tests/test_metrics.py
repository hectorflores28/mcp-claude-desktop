import pytest
from unittest.mock import Mock, patch
from app.core.metrics import ClaudeMetrics

@pytest.fixture
def metrics():
    with patch('prometheus_client.Counter'), \
         patch('prometheus_client.Histogram'), \
         patch('prometheus_client.Gauge'):
        metrics = ClaudeMetrics()
        metrics.requests_total = Mock()
        metrics.tokens_total = Mock()
        metrics.request_duration = Mock()
        metrics.active_requests = Mock()
        metrics.rate_limit_remaining = Mock()
        return metrics

def test_track_request_start(metrics):
    """Test que verifica el registro del inicio de solicitudes"""
    endpoint = "completion"
    model = "claude-3-opus"
    
    metrics.track_request_start(endpoint, model)
    
    metrics.active_requests.labels.assert_called_once_with(model=model)
    metrics.active_requests.labels().inc.assert_called_once()
    metrics.requests_total.labels.assert_called_once_with(endpoint=endpoint, model=model)
    metrics.requests_total.labels().inc.assert_called_once()

def test_track_request_end(metrics):
    """Test que verifica el registro del fin de solicitudes"""
    endpoint = "completion"
    model = "claude-3-opus"
    duration = 1.5
    
    metrics.track_request_end(endpoint, model, duration)
    
    metrics.active_requests.labels.assert_called_once_with(model=model)
    metrics.active_requests.labels().dec.assert_called_once()
    metrics.request_duration.labels.assert_called_once_with(endpoint=endpoint, model=model)
    metrics.request_duration.labels().observe.assert_called_once_with(duration)

def test_track_tokens(metrics):
    """Test que verifica el registro de tokens"""
    count = 100
    token_type = "prompt"
    model = "claude-3-opus"
    
    metrics.track_tokens(count, token_type, model)
    
    metrics.tokens_total.labels.assert_called_once_with(type=token_type, model=model)
    metrics.tokens_total.labels().inc.assert_called_once_with(count)

def test_update_rate_limit(metrics):
    """Test que verifica la actualización del límite de tasa"""
    remaining = 50
    model = "claude-3-opus"
    
    metrics.update_rate_limit(remaining, model)
    
    metrics.rate_limit_remaining.labels.assert_called_once_with(model=model)
    metrics.rate_limit_remaining.labels().set.assert_called_once_with(remaining)

def test_track_error(metrics):
    """Test que verifica el registro de errores"""
    endpoint = "completion"
    model = "claude-3-opus"
    error_type = "rate_limit"
    
    metrics.track_error(endpoint, model, error_type)
    
    metrics.requests_total.labels.assert_called_once_with(
        endpoint=f"{endpoint}_error_{error_type}",
        model=model
    )
    metrics.requests_total.labels().inc.assert_called_once() 