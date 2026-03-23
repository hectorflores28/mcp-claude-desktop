from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import verify_token, verify_api_key
from app.core.logging import LogManager
from typing import Optional
from app.core.blacklist import blacklist

security = HTTPBearer()

async def verify_auth(request: Request) -> Optional[dict]:
    """
    Verifica la autenticación de la solicitud.
    
    Args:
        request: Solicitud HTTP
        
    Returns:
        Datos del token si la autenticación es exitosa, None en caso contrario
        
    Raises:
        HTTPException: Si la autenticación falla
    """
    # Verificar si la ruta es pública
    if request.url.path in ["/api/health", "/docs", "/redoc", "/openapi.json"]:
        return None
    
    # Obtener el encabezado de autorización
    auth_header = request.headers.get("Authorization")
    
    if not auth_header:
        LogManager.log_warning("auth", "Solicitud sin encabezado de autorización")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere autenticación",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar el formato del encabezado
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        LogManager.log_warning("auth", "Formato de autorización inválido")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Formato de autorización inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    
    # Verificar si es un token JWT o una API key
    if len(token) > 100:  # Asumimos que los tokens JWT son más largos que las API keys
        try:
            # Verificar si el token está en la lista negra
            if await blacklist.is_blacklisted(token):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revocado")
            
            # Verificar token JWT
            payload = verify_token(token)
            LogManager.log_info("auth", f"Autenticación JWT exitosa para {payload.get('sub', 'unknown')}")
            return payload
        except HTTPException as e:
            LogManager.log_error("auth", f"Error de autenticación JWT: {str(e)}")
            raise
    else:
        # Verificar API key
        if verify_api_key(token):
            LogManager.log_info("auth", "Autenticación con API key exitosa")
            return {"sub": "api_key", "type": "api_key"}
        else:
            LogManager.log_warning("auth", "API key inválida")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key inválida",
                headers={"WWW-Authenticate": "Bearer"},
            )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Obtiene el usuario actual del token
    """
    try:
        token = credentials.credentials
        
        # Verificar lista negra
        if await blacklist.is_blacklisted(token):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revocado")
            
        # Verificar y decodificar token
        user = verify_token(token)
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        LogManager.log_error("auth", f"Error al obtener usuario: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Error de autenticación") 