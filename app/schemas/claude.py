from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum

class AnalysisType(str, Enum):
    """
    Tipos de análisis soportados
    """
    GENERAL = "general"
    SENTIMENT = "sentiment"
    TOPICS = "topics"
    SUMMARY = "summary"
    KEY_POINTS = "key_points"
    SUGGESTIONS = "suggestions"

class FormatType(str, Enum):
    """
    Tipos de formato soportados
    """
    MARKDOWN = "markdown"
    HTML = "html"
    TEXT = "text"
    JSON = "json"

class ClaudeRequest(BaseModel):
    """
    Esquema para solicitudes a Claude API
    """
    text: str = Field(..., description="Texto a procesar", min_length=1, max_length=100000)
    analysis_type: Optional[AnalysisType] = Field(None, description="Tipo de análisis a realizar")
    format_type: Optional[FormatType] = Field(FormatType.TEXT, description="Tipo de formato para la respuesta")
    max_tokens: Optional[int] = Field(None, description="Número máximo de tokens", ge=1, le=100000)
    temperature: Optional[float] = Field(0.7, description="Temperatura para la generación", ge=0.0, le=1.0)
    
    @validator("text")
    def validate_text(cls, v):
        """
        Valida que el texto no esté vacío
        """
        if not v.strip():
            raise ValueError("El texto no puede estar vacío")
        return v
    
    @validator("max_tokens")
    def validate_max_tokens(cls, v):
        """
        Valida el número máximo de tokens
        """
        if v is not None and v < 1:
            raise ValueError("El número máximo de tokens debe ser mayor que 0")
        return v
    
    @validator("temperature")
    def validate_temperature(cls, v):
        """
        Valida la temperatura
        """
        if v < 0.0 or v > 1.0:
            raise ValueError("La temperatura debe estar entre 0.0 y 1.0")
        return v

class ClaudeResponse(BaseModel):
    """
    Esquema para respuestas de Claude API
    """
    content: str = Field(..., description="Contenido generado")
    tokens_used: int = Field(..., description="Número de tokens utilizados", ge=0)
    model: str = Field(..., description="Modelo utilizado")
    execution_time: Optional[float] = Field(None, description="Tiempo de ejecución en segundos")
    analysis: Optional["ClaudeAnalysis"] = Field(None, description="Resultado del análisis si se solicitó")
    
    @validator("content")
    def validate_content(cls, v):
        """
        Valida que el contenido no esté vacío
        """
        if not v.strip():
            raise ValueError("El contenido no puede estar vacío")
        return v
    
    @validator("tokens_used")
    def validate_tokens_used(cls, v):
        """
        Valida el número de tokens utilizados
        """
        if v < 0:
            raise ValueError("El número de tokens utilizados no puede ser negativo")
        return v

class ClaudeAnalysis(BaseModel):
    """
    Esquema para resultados de análisis de Claude API
    """
    summary: str = Field(..., description="Resumen del análisis")
    key_points: List[str] = Field(default_factory=list, description="Puntos clave identificados")
    sentiment: str = Field(..., description="Sentimiento detectado (positivo, negativo, neutral)")
    topics: List[str] = Field(default_factory=list, description="Temas principales identificados")
    suggestions: List[str] = Field(default_factory=list, description="Sugerencias generadas")
    
    @validator("summary")
    def validate_summary(cls, v):
        """
        Valida que el resumen no esté vacío
        """
        if not v.strip():
            raise ValueError("El resumen no puede estar vacío")
        return v
    
    @validator("sentiment")
    def validate_sentiment(cls, v):
        """
        Valida el sentimiento
        """
        valid_sentiments = ["positivo", "negativo", "neutral"]
        if v.lower() not in valid_sentiments:
            raise ValueError(f"El sentimiento debe ser uno de: {', '.join(valid_sentiments)}")
        return v.lower()

class ClaudeToolSchema(BaseModel):
    """
    Esquema para herramientas de Claude API
    """
    name: str = Field(..., description="Nombre de la herramienta")
    description: str = Field(..., description="Descripción de la herramienta")
    parameters: Dict[str, Any] = Field(..., description="Parámetros de la herramienta")
    
    @validator("name")
    def validate_name(cls, v):
        """
        Valida el nombre de la herramienta
        """
        if not v.strip():
            raise ValueError("El nombre de la herramienta no puede estar vacío")
        return v
    
    @validator("description")
    def validate_description(cls, v):
        """
        Valida la descripción de la herramienta
        """
        if not v.strip():
            raise ValueError("La descripción de la herramienta no puede estar vacía")
        return v
    
    @validator("parameters")
    def validate_parameters(cls, v):
        """
        Valida los parámetros de la herramienta
        """
        if not isinstance(v, dict):
            raise ValueError("Los parámetros deben ser un diccionario")
        return v 