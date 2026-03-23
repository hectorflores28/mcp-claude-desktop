import os
import time
import json
import asyncio
from typing import Dict, Any, Optional, List
import backoff
from functools import lru_cache
import httpx
from app.core.config import settings
from app.core.logging import LogManager
from app.core.cache import get_cache

class ClaudeClient:
    """
    Cliente para interactuar con Claude API con soporte para caché y reintentos
    """
    def __init__(self):
        self.logger = LogManager.get_logger("claude_client")
        self.api_key = settings.CLAUDE_API_KEY
        if not self.api_key:
            raise ValueError("CLAUDE_API_KEY no encontrada en variables de entorno")
        
        # Configurar cliente HTTP personalizado
        self.http_client = httpx.Client(
            timeout=30.0,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        )
        
        self.model = settings.CLAUDE_MODEL
        self.max_tokens = settings.CLAUDE_MAX_TOKENS
        self.temperature = settings.CLAUDE_TEMPERATURE
        self._cache = get_cache()
        self._cache_ttl = 3600  # 1 hora por defecto
    
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        max_time=10
    )
    async def generate_response(self, prompt: str, max_tokens: Optional[int] = None, 
                              temperature: Optional[float] = None, 
                              cache_enabled: bool = True, 
                              cache_ttl: Optional[int] = None) -> Dict[str, Any]:
        """
        Genera una respuesta usando Claude API con soporte para caché y reintentos
        
        Args:
            prompt: Prompt para Claude
            max_tokens: Número máximo de tokens (opcional)
            temperature: Temperatura para la generación (opcional)
            cache_enabled: Si se debe usar caché (opcional)
            cache_ttl: Tiempo de vida del caché en segundos (opcional)
            
        Returns:
            Dict con la respuesta de Claude
        """
        if not prompt:
            raise ValueError("El prompt no puede estar vacío")
        
        # Usar valores proporcionados o los predeterminados
        tokens = max_tokens or self.max_tokens
        temp = temperature or self.temperature
        ttl = cache_ttl or self._cache_ttl
        
        # Generar clave de caché
        cache_key = f"claude:response:{hash(prompt + str(tokens) + str(temp))}"
        
        # Intentar obtener del caché si está habilitado
        if cache_enabled:
            cached_response = await self._cache.get(cache_key)
            if cached_response:
                self.logger.info(f"Respuesta obtenida del caché para prompt: {prompt[:50]}...")
                return cached_response
        
        start_time = time.time()
        try:
            # Preparar datos para la petición
            data = {
                "model": self.model,
                "max_tokens": tokens,
                "temperature": temp,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            # Hacer la petición directamente con httpx
            response = self.http_client.post(
                "https://api.anthropic.com/v1/messages",
                json=data
            )
            response.raise_for_status()
            result = response.json()
            
            response_time = time.time() - start_time
            
            # Formatear respuesta
            formatted_result = {
                "content": result["content"][0]["text"],
                "tokens_used": result["usage"]["total_tokens"],
                "model": self.model,
                "execution_time": response_time
            }
            
            # Guardar en caché si está habilitado
            if cache_enabled:
                await self._cache.set(cache_key, formatted_result, ttl=ttl)
            
            self.logger.info(f"Respuesta generada en {response_time:.2f}s usando {formatted_result['tokens_used']} tokens")
            return formatted_result
            
        except Exception as e:
            self.logger.error(f"Error al generar respuesta: {str(e)}")
            raise
        finally:
            # Cerrar el cliente HTTP
            self.http_client.close()
    
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        max_time=10
    )
    async def analyze_text(self, text: str, analysis_type: str = "general") -> Dict[str, Any]:
        """
        Analiza un texto usando Claude API
        
        Args:
            text: Texto a analizar
            analysis_type: Tipo de análisis a realizar
            
        Returns:
            Dict con el resultado del análisis
        """
        if not text:
            raise ValueError("El texto no puede estar vacío")
        
        # Generar prompt según el tipo de análisis
        if analysis_type == "general":
            prompt = f"Analiza el siguiente texto y proporciona un resumen, puntos clave, sentimiento y temas principales:\n\n{text}"
        elif analysis_type == "sentiment":
            prompt = f"Analiza el sentimiento del siguiente texto y proporciona una clasificación (positivo, negativo, neutral) con explicación:\n\n{text}"
        elif analysis_type == "topics":
            prompt = f"Identifica los temas principales del siguiente texto y proporciona una lista con explicación:\n\n{text}"
        else:
            prompt = f"Analiza el siguiente texto según el tipo '{analysis_type}' y proporciona resultados detallados:\n\n{text}"
        
        # Generar respuesta
        response = await self.generate_response(prompt, cache_enabled=False)
        
        # Formatear resultado
        result = {
            "analysis_type": analysis_type,
            "content": response["content"],
            "tokens_used": response["tokens_used"],
            "model": response["model"]
        }
        
        return result

# Instancia global del cliente Claude
@lru_cache()
def get_claude_client() -> ClaudeClient:
    """
    Obtiene una instancia global del cliente Claude
    
    Returns:
        ClaudeClient: Instancia del cliente Claude
    """
    return ClaudeClient() 