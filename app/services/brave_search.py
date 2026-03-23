import aiohttp
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.logging import LogManager
from app.schemas.search import SearchResult, SearchResponse, SearchAnalysis
from app.core.prompts import PromptTemplates
from app.services.claude_service import ClaudeService

class BraveSearch:
    """
    Servicio para realizar búsquedas usando Brave Search API
    """
    BASE_URL = "https://api.search.brave.com/res/v1/web/search"
    
    def __init__(self):
        self.api_key = settings.BRAVE_SEARCH_API_KEY
        self.headers = {
            "X-Subscription-Token": self.api_key,
            "Accept": "application/json"
        }
        self.claude_service = ClaudeService()
    
    async def search(
        self,
        query: str,
        num_results: int = 5,
        country: str = "ES",
        language: str = "es",
        analyze: bool = False
    ) -> SearchResponse:
        """
        Realiza una búsqueda usando Brave Search API
        
        Args:
            query: Término de búsqueda
            num_results: Número de resultados a devolver
            country: Código de país para resultados
            language: Código de idioma para resultados
            analyze: Si se debe analizar los resultados con Claude
            
        Returns:
            SearchResponse con los resultados y análisis opcional
        """
        try:
            # Registrar la búsqueda
            LogManager.log_search(query, [])
            
            # Construir parámetros de búsqueda
            params = {
                "q": query,
                "count": num_results,
                "country": country,
                "language": language
            }
            
            # Realizar la búsqueda
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.BASE_URL,
                    headers=self.headers,
                    params=params
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        LogManager.log_error(
                            "brave_search",
                            f"Error en búsqueda: {error_text}"
                        )
                        raise Exception(f"Error en búsqueda: {error_text}")
                    
                    data = await response.json()
                    
                    # Procesar resultados
                    results = []
                    for item in data.get("web", {}).get("results", []):
                        result = SearchResult(
                            title=item.get("title", ""),
                            url=item.get("url", ""),
                            description=item.get("description", ""),
                            source=item.get("source", ""),
                            published_date=item.get("published_date"),
                            snippet=item.get("snippet")
                        )
                        results.append(result)
                    
                    # Crear respuesta
                    search_response = SearchResponse(
                        query=query,
                        results=results,
                        total_results=len(results)
                    )
                    
                    # Analizar resultados si se solicita
                    if analyze and results:
                        analysis = await self._analyze_results(query, results)
                        search_response.analysis = analysis
                        
                        # Guardar análisis en archivo Markdown
                        await self._save_analysis_to_markdown(query, analysis)
                    
                    return search_response
                    
        except Exception as e:
            LogManager.log_error("brave_search", str(e))
            raise
    
    async def _analyze_results(
        self,
        query: str,
        results: List[SearchResult]
    ) -> SearchAnalysis:
        """
        Analiza los resultados de búsqueda usando Claude
        
        Args:
            query: Término de búsqueda original
            results: Lista de resultados a analizar
            
        Returns:
            SearchAnalysis con el análisis de los resultados
        """
        try:
            # Formatear resultados para el prompt
            results_text = "\n\n".join([
                f"Título: {r.title}\nURL: {r.url}\nDescripción: {r.description}"
                for r in results
            ])
            
            # Obtener prompt para análisis
            prompt = PromptTemplates.get_search_summary_prompt(query, results_text)
            
            # Analizar con Claude
            analysis_text = await self.claude_service.analyze_text(
                text=results_text,
                analysis_type="search_results"
            )
            
            # Parsear el análisis
            return SearchAnalysis(
                summary=analysis_text.summary,
                key_points=analysis_text.key_points,
                relevance_score=analysis_text.relevance_score,
                suggested_queries=analysis_text.suggested_queries
            )
            
        except Exception as e:
            LogManager.log_error("brave_search", f"Error en análisis: {str(e)}")
            raise
            
    async def _save_analysis_to_markdown(self, query: str, analysis: SearchAnalysis):
        """
        Guarda el análisis en un archivo Markdown
        
        Args:
            query: Término de búsqueda original
            analysis: Análisis a guardar
        """
        try:
            # Crear contenido Markdown
            content = f"""# Análisis de búsqueda: {query}

## Resumen
{analysis.summary}

## Puntos clave
{chr(10).join([f"- {point}" for point in analysis.key_points])}

## Puntuación de relevancia
{analysis.relevance_score}

## Consultas sugeridas
{chr(10).join([f"- {query}" for query in analysis.suggested_queries])}
"""
            
            # Guardar archivo
            filename = f"search_analysis_{query.replace(' ', '_')}.md"
            with open(f"{settings.DATA_DIR}/{filename}", "w", encoding="utf-8") as f:
                f.write(content)
                
            LogManager.log_info(f"Análisis guardado en {filename}")
            
        except Exception as e:
            LogManager.log_error("brave_search", f"Error al guardar análisis: {str(e)}")
            raise 