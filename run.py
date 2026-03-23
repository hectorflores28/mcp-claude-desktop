import uvicorn
import os
import sys
import platform
from app.core.config import settings
from app.core.logging import LogManager

def main():
    # Configurar logging
    LogManager.setup_logger()
    LogManager.log_info("Iniciando servidor MCP Claude...")
    
    try:
        # Configuración de uvicorn
        config = uvicorn.Config(
            "app.main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,
            log_level="info",
            access_log=True,
            workers=1,
            limit_concurrency=100,
            timeout_keep_alive=5
        )
        
        # Iniciar servidor
        server = uvicorn.Server(config)
        server.run()
        
    except KeyboardInterrupt:
        LogManager.log_info("Servidor detenido por el usuario")
        if platform.system() == 'Windows':
            os._exit(0)
        else:
            sys.exit(0)
    except Exception as e:
        LogManager.log_error("Error", f"Error al iniciar el servidor: {str(e)}")
        raise
    finally:
        LogManager.log_info("Cerrando servidor...")
        if platform.system() == 'Windows':
            os._exit(0)
        else:
            sys.exit(0)

if __name__ == "__main__":
    main() 