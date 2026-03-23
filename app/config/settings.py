"""
Configuración centralizada para MCP-Claude.

Este módulo proporciona una configuración centralizada para toda la aplicación,
cargando valores desde variables de entorno con valores predeterminados.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Configuración de la aplicación."""
    
    # Configuración general
    APP_NAME: str = Field(default="MCP-Claude", env="APP_NAME")
    API_V1_STR: str = Field(default="/api", env="API_V1_STR")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    VERSION: str = Field(default="1.1.0", env="VERSION")
    PROJECT_NAME: str = Field(default="MCP-Claude", env="PROJECT_NAME")
    
    # Configuración del servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    API_PREFIX: str = "/api"
    CORS_ORIGINS: str = "http://127.0.0.1:8080,http://localhost:8080,http://127.0.0.1:3000,http://localhost:3000"
    WORKERS: int = Field(default=1, env="WORKERS")
    
    # Seguridad
    API_KEY: str = Field(default="8Bg2auvsn1uVZfW9g8ybxZhkJRtc1cRyRctvv5MyniM", env="API_KEY")
    JWT_SECRET_KEY: str = Field(default="0r0HAtFJfCVpqYOl2h7vJQR1ggxJ5MBAUlPO8dLXav4", env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_ISSUER: str = Field(default="mcp-claude", env="JWT_ISSUER")
    JWT_AUDIENCE: str = Field(default="claude-desktop", env="JWT_AUDIENCE")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Claude API
    CLAUDE_API_KEY: str = Field(default="", env="CLAUDE_API_KEY")
    CLAUDE_MODEL: str = Field(default="claude-3-opus-20240229", env="CLAUDE_MODEL")
    CLAUDE_MAX_TOKENS: int = Field(default=4096, env="CLAUDE_MAX_TOKENS")
    CLAUDE_TEMPERATURE: float = Field(default=0.7, env="CLAUDE_TEMPERATURE")
    
    # Brave Search API
    BRAVE_SEARCH_API_KEY: str = Field(default="", env="BRAVE_SEARCH_API_KEY")
    BRAVE_SEARCH_BASE_URL: str = Field(default="https://api.search.brave.com/res/v1/web/search", env="BRAVE_SEARCH_BASE_URL")
    
    # Sistema de archivos
    DATA_DIR: str = Field(default="./data", env="DATA_DIR")
    LOG_DIR: str = Field(default="./logs", env="LOG_DIR")
    TEMP_DIR: str = Field(default="./temp", env="TEMP_DIR")
    PLUGIN_DIR: str = Field(default="./plugins", env="PLUGIN_DIR")
    ALLOWED_EXTENSIONS: List[str] = Field(default=["md", "txt", "json"], env="ALLOWED_EXTENSIONS")
    MAX_FILE_SIZE: int = Field(default=10485760, env="MAX_FILE_SIZE")  # 10MB en bytes
    
    # Configuración de Claude
    MAX_TOKENS: int = Field(default=4096, env="MAX_TOKENS")
    TEMPERATURE: float = Field(default=0.7, env="TEMPERATURE")
    
    # Configuración de búsqueda
    DEFAULT_SEARCH_RESULTS: int = Field(default=5, env="DEFAULT_SEARCH_RESULTS")
    DEFAULT_SEARCH_COUNTRY: str = Field(default="ES", env="DEFAULT_SEARCH_COUNTRY")
    DEFAULT_SEARCH_LANGUAGE: str = Field(default="es", env="DEFAULT_SEARCH_LANGUAGE")
    
    # File System
    UPLOAD_DIR: str = Field(default="uploads", env="UPLOAD_DIR")
    
    # Configuración de logging
    LOG_FORMAT: str = Field(default="markdown", env="LOG_FORMAT")
    LOG_MAX_BYTES: int = Field(default=10485760, env="LOG_MAX_BYTES")  # 10MB
    LOG_BACKUP_COUNT: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    # Rate Limiting
    RATE_LIMIT_WINDOW: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # segundos
    RATE_LIMIT_MAX_REQUESTS: int = Field(default=100, env="RATE_LIMIT_MAX_REQUESTS")
    
    # Redis
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_SSL: bool = Field(default=False, env="REDIS_SSL")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_TIMEOUT: int = Field(default=5, env="REDIS_TIMEOUT")
    REDIS_MAX_CONNECTIONS: int = Field(default=10, env="REDIS_MAX_CONNECTIONS")
    
    # Caché
    CACHE_TTL: int = Field(default=300, env="CACHE_TTL")  # 5 minutos
    CACHE_PREFIX: str = Field(default="mcp:", env="CACHE_PREFIX")
    
    # Plugins
    PLUGINS_ENABLED: bool = Field(default=True, env="PLUGINS_ENABLED")
    PLUGIN_HOOKS: List[str] = Field(
        default=[
            "mcp_before_execute",
            "mcp_after_execute",
            "mcp_before_search",
            "mcp_after_search",
            "mcp_before_file_read",
            "mcp_after_file_read",
            "mcp_before_file_write",
            "mcp_after_file_write",
            "mcp_error",
            "mcp_startup",
            "mcp_shutdown"
        ],
        env="PLUGIN_HOOKS"
    )
    
    # Configuración de la terminal de Windows
    PYTHONUNBUFFERED: str = Field(default="1", env="PYTHONUNBUFFERED")
    PYTHONIOENCODING: str = Field(default="utf-8", env="PYTHONIOENCODING")
    
    @validator("ALLOWED_EXTENSIONS", pre=True)
    def parse_allowed_extensions(cls, v):
        """Parsea la lista de extensiones permitidas."""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v
    
    @validator("PLUGIN_HOOKS", pre=True)
    def parse_plugin_hooks(cls, v):
        """Parsea la lista de hooks de plugins."""
        if isinstance(v, str):
            return [hook.strip() for hook in v.split(",")]
        return v
    
    class Config:
        """Configuración de Pydantic."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Instancia global de configuración
settings = Settings()

# Crear directorios necesarios
for directory in [settings.DATA_DIR, settings.LOG_DIR, settings.TEMP_DIR, settings.PLUGIN_DIR]:
    Path(directory).mkdir(parents=True, exist_ok=True) 