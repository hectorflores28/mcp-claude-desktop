import os
import time
import json
import asyncio
from typing import Dict, Any, Optional, List
import backoff
from functools import lru_cache
from app.core.config import settings
from app.core.logging import LogManager
from app.core.prompts import PromptTemplates
from app.schemas.search import SearchAnalysis
from app.core.markdown_logger import MarkdownLogger
from app.core.claude_client import get_claude_client
from app.core.cache import get_cache
from app.core.metrics import MetricsCollector
from app.schemas.claude import ClaudeRequest, ClaudeResponse, ClaudeAnalysis

class ClaudeService:
    """
    Servicio para interactuar con Claude API con soporte para caché y reintentos
    """
    def __init__(self):
        self.logger = LogManager.get_logger("claude_service")
        self.client = get_claude_client()
        self._cache = get_cache()
        self._cache_ttl = 3600  # 1 hora por defecto
        self._metrics = MetricsCollector()
        self.model = settings.CLAUDE_MODEL
        self.max_tokens = settings.CLAUDE_MAX_TOKENS
        self.temperature = settings.CLAUDE_TEMPERATURE
        self.markdown_logger = MarkdownLogger()
    
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        max_time=10
    )
    async def mcp_completion(self, request: ClaudeRequest) -> ClaudeResponse:
        """
        Procesa una solicitud de completado usando Claude API
        
        Args:
            request: Solicitud de completado
            
        Returns:
            ClaudeResponse con la respuesta generada
        """
        start_time = time.time()
        
        try:
            # Generar respuesta con Claude
            response = await self.client.generate_response(
                prompt=request.text,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                cache_enabled=True,
                cache_ttl=self._cache_ttl
            )
            
            # Registrar métricas
            await self._metrics.record_api_call(
                endpoint="mcp_completion",
                method="POST",
                status_code=200,
                response_time=time.time() - start_time
            )
            
            # Formatear respuesta
            result = ClaudeResponse(
                content=response["content"],
                tokens_used=response["tokens_used"],
                model=response["model"]
            )
            
            # Añadir análisis si se solicita
            if request.analysis_type:
                analysis = await self.analyze_text(request.text, request.analysis_type)
                result.analysis = analysis
            
            return result
            
        except Exception as e:
            # Registrar error en métricas
            await self._metrics.record_api_call(
                endpoint="mcp_completion",
                method="POST",
                status_code=500,
                response_time=time.time() - start_time
            )
            
            self.logger.error(f"Error al procesar solicitud de completado: {str(e)}")
            raise
    
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        max_time=10
    )
    async def analyze_text(self, text: str, analysis_type: str = "general") -> ClaudeAnalysis:
        """
        Analiza un texto usando Claude API
        
        Args:
            text: Texto a analizar
            analysis_type: Tipo de análisis a realizar
            
        Returns:
            ClaudeAnalysis con el resultado del análisis
        """
        start_time = time.time()
        
        try:
            # Generar análisis con Claude
            response = await self.client.analyze_text(text, analysis_type)
            
            # Registrar métricas
            await self._metrics.record_api_call(
                endpoint="analyze_text",
                method="POST",
                status_code=200,
                response_time=time.time() - start_time
            )
            
            # Formatear resultado
            result = ClaudeAnalysis(
                summary=response["content"],
                key_points=[],  # TODO: Extraer puntos clave del contenido
                sentiment="neutral",  # TODO: Extraer sentimiento del contenido
                topics=[],  # TODO: Extraer temas del contenido
                suggestions=[]  # TODO: Extraer sugerencias del contenido
            )
            
            return result
            
        except Exception as e:
            # Registrar error en métricas
            await self._metrics.record_api_call(
                endpoint="analyze_text",
                method="POST",
                status_code=500,
                response_time=time.time() - start_time
            )
            
            self.logger.error(f"Error al analizar texto: {str(e)}")
            raise
    
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        max_time=10
    )
    async def get_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado del servicio Claude
        
        Returns:
            Dict con información del estado
        """
        try:
            # Obtener estado de Claude
            status = {
                "status": "online",
                "model": self.client.model,
                "max_tokens": self.client.max_tokens,
                "temperature": self.client.temperature,
                "cache_enabled": True,
                "cache_ttl": self._cache_ttl
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error al obtener estado: {str(e)}")
            raise
    
    async def generate_markdown(
        self,
        content: str,
        format_type: str = "article",
        save: bool = False,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Genera contenido en formato Markdown usando Claude
        
        Args:
            content: Contenido a formatear
            format_type: Tipo de formato (article, documentation, etc.)
            save: Si se debe guardar el archivo
            filename: Nombre del archivo a guardar
            
        Returns:
            Dict con el contenido generado y metadata
        """
        try:
            # Obtener prompt para generación
            prompt = PromptTemplates.get_markdown_generation_prompt(
                content=content,
                format_type=format_type
            )
            
            # Generar contenido con Claude
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extraer contenido generado
            generated_content = response.content[0].text
            
            # Registrar operación
            LogManager.log_claude_operation(
                "generate_markdown",
                prompt,
                generated_content
            )
            
            result = {
                "content": generated_content,
                "format_type": format_type,
                "model": self.model
            }
            
            # Guardar archivo si se solicita
            if save and filename:
                await self.markdown_logger.log_file_operation(
                    operation="create",
                    filename=filename,
                    content=generated_content
                )
                result["saved"] = True
                result["filename"] = filename
            
            return result
            
        except Exception as e:
            LogManager.log_error("claude", str(e))
            raise
    
    async def edit_markdown(
        self,
        content: str,
        instructions: str
    ) -> Dict[str, Any]:
        """
        Edita contenido Markdown usando Claude
        
        Args:
            content: Contenido original
            instructions: Instrucciones de edición
            
        Returns:
            Dict con el contenido editado y metadata
        """
        try:
            # Obtener prompt para edición
            prompt = PromptTemplates.get_file_edit_prompt(
                content=content,
                instructions=instructions
            )
            
            # Generar edición con Claude
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extraer contenido editado
            edited_content = response.content[0].text
            
            # Registrar operación
            LogManager.log_claude_operation(
                "edit_markdown",
                prompt,
                edited_content
            )
            
            return {
                "content": edited_content,
                "original_content": content,
                "instructions": instructions,
                "model": self.model
            }
            
        except Exception as e:
            LogManager.log_error("claude", str(e))
            raise

# Instancia global del servicio Claude
@lru_cache()
def get_claude_service() -> ClaudeService:
    """
    Obtiene una instancia global del servicio Claude
    
    Returns:
        ClaudeService: Instancia del servicio Claude
    """
    return ClaudeService() 