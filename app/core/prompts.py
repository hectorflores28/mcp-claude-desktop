from typing import Dict, List, Optional, Any
from app.schemas.mcp import MCPPromptTemplate

class PromptTemplates:
    """
    Plantillas de prompts para diferentes operaciones
    """
    
    @staticmethod
    def get_templates() -> List[MCPPromptTemplate]:
        """Obtiene todas las plantillas de prompts disponibles."""
        return [
            MCPPromptTemplate(
                name="analisis_busqueda",
                description="Analiza los resultados de una búsqueda web",
                template="""Analiza los siguientes resultados de búsqueda para la consulta: "{query}"

Resultados:
{results}

Por favor, proporciona:
1. Un resumen general de los resultados
2. Los puntos más importantes encontrados
3. Cualquier patrón o tendencia notable
4. Recomendaciones basadas en la información""",
                parameters=["query", "results"]
            ),
            MCPPromptTemplate(
                name="generar_markdown",
                description="Genera contenido en formato Markdown",
                template="""Convierte el siguiente contenido en un documento Markdown
del tipo {format_type}:

{content}

Asegúrate de:
1. Usar los encabezados apropiados
2. Formatear listas y tablas correctamente
3. Incluir enlaces cuando sea relevante
4. Mantener un estilo consistente""",
                parameters=["content", "format_type"]
            ),
            MCPPromptTemplate(
                name="resumen_documento",
                description="Genera un resumen de un documento",
                template="""Genera un resumen conciso del siguiente documento:

{content}

El resumen debe:
1. Capturar los puntos principales
2. Mantener la estructura lógica
3. Ser aproximadamente el 20% de la longitud original
4. Incluir conclusiones clave""",
                parameters=["content"]
            ),
            MCPPromptTemplate(
                name="extraer_conceptos",
                description="Extrae conceptos clave de un texto",
                template="""Extrae los conceptos clave del siguiente texto:

{content}

Para cada concepto:
1. Identifica el término principal
2. Proporciona una definición breve
3. Indica su importancia en el contexto
4. Relaciónalo con otros conceptos mencionados""",
                parameters=["content"]
            )
        ]
    
    @staticmethod
    def get_template(name: str) -> Optional[MCPPromptTemplate]:
        """Obtiene una plantilla específica por nombre."""
        for template in PromptTemplates.get_templates():
            if template.name == name:
                return template
        return None
    
    @staticmethod
    def format_template(name: str, **kwargs) -> Optional[str]:
        """Formatea una plantilla con los parámetros proporcionados."""
        template = PromptTemplates.get_template(name)
        if not template:
            return None
        
        try:
            return template.template.format(**kwargs)
        except KeyError as e:
            return f"Error al formatear la plantilla: {str(e)}"

    @staticmethod
    def format_prompt(template: str, **kwargs: Any) -> str:
        """
        Formatea un prompt con las variables proporcionadas
        """
        return template.format(**kwargs)
    
    # Prompts para análisis de texto
    TEXT_ANALYSIS = """
    Analiza el siguiente texto y proporciona un {analysis_type}:
    
    Texto: {text}
    
    Por favor, proporciona el análisis en formato Markdown.
    """
    
    # Prompts para generación de Markdown
    MARKDOWN_GENERATION = """
    Genera contenido en formato Markdown para el siguiente texto, 
    siguiendo el estilo de {format_type}:
    
    Contenido: {content}
    
    Asegúrate de:
    1. Usar encabezados apropiados
    2. Incluir listas cuando sea necesario
    3. Formatear código si está presente
    4. Añadir enlaces relevantes
    5. Mantener un estilo consistente
    """
    
    # Prompts para resumen de búsqueda
    SEARCH_SUMMARY = """
    Analiza los siguientes resultados de búsqueda y proporciona un resumen conciso:
    
    Consulta: {query}
    Resultados:
    {results}
    
    Por favor, proporciona:
    1. Un resumen general
    2. Puntos clave encontrados
    3. Conclusiones relevantes
    """
    
    # Prompts para edición de archivos
    FILE_EDIT = """
    Edita el siguiente contenido en formato Markdown según las instrucciones:
    
    Contenido original:
    {content}
    
    Instrucciones de edición:
    {instructions}
    
    Mantén el formato Markdown y asegúrate de preservar la estructura original.
    """
    
    @classmethod
    def get_text_analysis_prompt(cls, text: str, analysis_type: str) -> str:
        """
        Genera un prompt para análisis de texto
        """
        return cls.format_prompt(
            cls.TEXT_ANALYSIS,
            text=text,
            analysis_type=analysis_type
        )
    
    @classmethod
    def get_markdown_generation_prompt(cls, content: str, format_type: str) -> str:
        """
        Genera un prompt para generación de Markdown
        """
        return cls.format_prompt(
            cls.MARKDOWN_GENERATION,
            content=content,
            format_type=format_type
        )
    
    @classmethod
    def get_search_summary_prompt(cls, query: str, results: str) -> str:
        """
        Genera un prompt para resumen de búsqueda
        """
        return cls.format_prompt(
            cls.SEARCH_SUMMARY,
            query=query,
            results=results
        )
    
    @classmethod
    def get_file_edit_prompt(cls, content: str, instructions: str) -> str:
        """
        Genera un prompt para edición de archivos
        """
        return cls.format_prompt(
            cls.FILE_EDIT,
            content=content,
            instructions=instructions
        ) 