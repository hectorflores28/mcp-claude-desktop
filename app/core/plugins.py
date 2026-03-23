"""
Gestor de plugins para el servidor MCP.

Este módulo proporciona la funcionalidad para cargar y gestionar plugins.
"""

import os
import importlib
import inspect
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel

from app.core.logging import LogManager
from app.core.config import settings

logger = LogManager.get_logger("core.plugins")

class Plugin(BaseModel):
    """Clase base para plugins."""
    name: str
    version: str
    description: str
    enabled: bool = True

    def initialize(self) -> None:
        """Inicializa el plugin."""
        pass

    def shutdown(self) -> None:
        """Apaga el plugin."""
        pass

class PluginManager:
    """Gestor de plugins."""
    
    def __init__(self):
        """Inicializa el gestor de plugins."""
        self.plugins: Dict[str, Plugin] = {}
        self.hooks: Dict[str, List[Callable]] = {}
        self._load_hooks()
    
    def _load_hooks(self) -> None:
        """Carga los hooks disponibles."""
        for hook in settings.PLUGIN_HOOKS:
            self.hooks[hook] = []
    
    def load_plugins(self) -> None:
        """Carga todos los plugins disponibles."""
        if not settings.PLUGINS_ENABLED:
            logger.info("Los plugins están deshabilitados")
            return
        
        plugin_dir = settings.PLUGIN_DIR
        if not os.path.exists(plugin_dir):
            os.makedirs(plugin_dir)
            logger.info(f"Directorio de plugins creado: {plugin_dir}")
            return
        
        for item in os.listdir(plugin_dir):
            plugin_path = os.path.join(plugin_dir, item)
            if os.path.isdir(plugin_path):
                try:
                    self._load_plugin(item)
                except Exception as e:
                    logger.error(f"Error al cargar el plugin {item}: {str(e)}")
    
    def _load_plugin(self, plugin_name: str) -> None:
        """
        Carga un plugin específico.
        
        Args:
            plugin_name: Nombre del plugin a cargar
        """
        try:
            module = importlib.import_module(f"plugins.{plugin_name}")
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, Plugin) and 
                    obj != Plugin):
                    plugin = obj()
                    plugin.initialize()
                    self.plugins[plugin_name] = plugin
                    logger.info(f"Plugin cargado: {plugin_name} v{plugin.version}")
                    break
        except Exception as e:
            logger.error(f"Error al cargar el plugin {plugin_name}: {str(e)}")
            raise
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """
        Obtiene un plugin por nombre.
        
        Args:
            name: Nombre del plugin
            
        Returns:
            El plugin si existe, None en caso contrario
        """
        return self.plugins.get(name)
    
    def enable_plugin(self, name: str) -> bool:
        """
        Habilita un plugin.
        
        Args:
            name: Nombre del plugin
            
        Returns:
            True si se habilitó correctamente, False en caso contrario
        """
        plugin = self.get_plugin(name)
        if plugin:
            plugin.enabled = True
            plugin.initialize()
            logger.info(f"Plugin habilitado: {name}")
            return True
        return False
    
    def disable_plugin(self, name: str) -> bool:
        """
        Deshabilita un plugin.
        
        Args:
            name: Nombre del plugin
            
        Returns:
            True si se deshabilitó correctamente, False en caso contrario
        """
        plugin = self.get_plugin(name)
        if plugin:
            plugin.enabled = False
            plugin.shutdown()
            logger.info(f"Plugin deshabilitado: {name}")
            return True
        return False
    
    def register_hook(self, hook_name: str, callback: Callable) -> None:
        """
        Registra un callback para un hook.
        
        Args:
            hook_name: Nombre del hook
            callback: Función a ejecutar
        """
        if hook_name in self.hooks:
            self.hooks[hook_name].append(callback)
    
    def execute_hook(self, hook_name: str, *args, **kwargs) -> Any:
        """
        Ejecuta todos los callbacks registrados para un hook.
        
        Args:
            hook_name: Nombre del hook
            *args: Argumentos posicionales
            **kwargs: Argumentos nombrados
            
        Returns:
            Resultado de la ejecución del hook
        """
        if hook_name not in self.hooks:
            return None
        
        results = []
        for callback in self.hooks[hook_name]:
            try:
                result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Error al ejecutar hook {hook_name}: {str(e)}")
        
        return results[0] if len(results) == 1 else results
    
    def shutdown(self) -> None:
        """Apaga todos los plugins."""
        for plugin in self.plugins.values():
            try:
                plugin.shutdown()
            except Exception as e:
                logger.error(f"Error al apagar el plugin {plugin.name}: {str(e)}")

# Instancia global del gestor de plugins
plugin_manager = PluginManager() 