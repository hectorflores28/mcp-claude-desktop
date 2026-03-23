from typing import Dict, Any
from pydantic import BaseModel, Field
from app.core.config import settings
import json
from datetime import datetime

class ClaudeDesktopConfig(BaseModel):
    """
    Configuración para Claude Desktop
    """
    version: str = Field(default="1.1.0", description="Versión del protocolo MCP")
    server_url: str = Field(default="http://localhost:8000", description="URL del servidor MCP")
    api_key: str = Field(default=settings.API_KEY, description="API Key para autenticación")
    model: str = Field(default=settings.CLAUDE_MODEL, description="Modelo de Claude a utilizar")
    max_tokens: int = Field(default=settings.CLAUDE_MAX_TOKENS, description="Máximo de tokens por respuesta")
    temperature: float = Field(default=settings.CLAUDE_TEMPERATURE, description="Temperatura para generación")
    plugins_enabled: bool = Field(default=settings.PLUGINS_ENABLED, description="Habilitar sistema de plugins")
    cache_enabled: bool = Field(default=True, description="Habilitar sistema de caché")
    rate_limit_enabled: bool = Field(default=True, description="Habilitar rate limiting")
    logging_enabled: bool = Field(default=True, description="Habilitar sistema de logging")
    blacklist_enabled: bool = Field(default=True, description="Habilitar lista negra de tokens")

    class Config:
        json_schema_extra = {
            "example": {
                "version": "1.1.0",
                "server_url": "http://localhost:8000",
                "api_key": "your-api-key-here",
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 4096,
                "temperature": 0.7,
                "plugins_enabled": True,
                "cache_enabled": True,
                "rate_limit_enabled": True,
                "logging_enabled": True,
                "blacklist_enabled": True
            }
        }

def get_claude_desktop_config() -> Dict[str, Any]:
    """
    Obtiene la configuración para Claude Desktop
    """
    config = ClaudeDesktopConfig()
    return config.dict()

def generate_claude_desktop_config_file() -> str:
    """
    Genera el archivo de configuración para Claude Desktop
    """
    config = get_claude_desktop_config()
    return f"""# Configuración de Claude Desktop para MCP
# Versión: {config['version']}
# Última actualización: {datetime.utcnow().isoformat()}

{json.dumps(config, indent=2)}
""" 