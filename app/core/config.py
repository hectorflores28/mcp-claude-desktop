import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Settings:
    # API Keys
    CLAUDE_API_KEY: str = os.getenv("CLAUDE_API_KEY", "")
    API_KEY: str = os.getenv("API_KEY", "your-api-key-here")
    
    # Configuración del servidor
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Configuración de logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Configuración de seguridad
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Configuración de Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_SSL: bool = os.getenv("REDIS_SSL", "false").lower() == "true"
    REDIS_TIMEOUT: int = int(os.getenv("REDIS_TIMEOUT", "5"))
    REDIS_MAX_CONNECTIONS: int = int(os.getenv("REDIS_MAX_CONNECTIONS", "10"))
    
    # Configuración de directorios
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    LOG_DIR: Path = BASE_DIR / os.getenv("LOG_DIR", "logs")
    DATA_DIR: Path = BASE_DIR / os.getenv("DATA_DIR", "data")
    TEMP_DIR: Path = BASE_DIR / os.getenv("TEMP_DIR", "temp")
    
    # Configuración de Claude
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-3-sonnet-20240229")
    CLAUDE_MAX_TOKENS: int = int(os.getenv("CLAUDE_MAX_TOKENS", "4096"))
    CLAUDE_TEMPERATURE: float = float(os.getenv("CLAUDE_TEMPERATURE", "0.7"))
    
    # Configuración de búsqueda
    DEFAULT_SEARCH_RESULTS: int = int(os.getenv("DEFAULT_SEARCH_RESULTS", "5"))
    DEFAULT_SEARCH_COUNTRY: str = os.getenv("DEFAULT_SEARCH_COUNTRY", "ES")
    DEFAULT_SEARCH_LANGUAGE: str = os.getenv("DEFAULT_SEARCH_LANGUAGE", "es")
    
    # Configuración del sistema de archivos
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))
    ALLOWED_EXTENSIONS: List[str] = os.getenv("ALLOWED_EXTENSIONS", "md,txt,json").split(",")
    UPLOAD_DIR: Path = BASE_DIR / os.getenv("UPLOAD_DIR", "uploads")
    
    # Configuración de CORS
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "http://127.0.0.1:3000,http://127.0.0.1:8000").split(",")

# Instancia global de configuración
settings = Settings() 