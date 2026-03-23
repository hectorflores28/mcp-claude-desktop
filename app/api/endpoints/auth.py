from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import (
    verify_api_key, create_access_token, verify_token, 
    blacklist_token, get_current_user
)
from app.core.config import settings
from app.core.logging import LogManager
from typing import Dict, Any
from datetime import timedelta

router = APIRouter()

@router.post("/token", response_model=Dict[str, Any])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Obtiene un token de acceso usando credenciales
    """
    # Verificar credenciales (en este caso, solo API key)
    if form_data.username != "api" or form_data.password != settings.API_KEY:
        LogManager.log_warning("auth", "Intento de acceso con credenciales inválidas")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crear token de acceso
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": "api", "type": "access_token"},
        expires_delta=access_token_expires
    )
    
    # Crear token de refresco
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_access_token(
        data={"sub": "api", "type": "refresh_token"},
        expires_delta=refresh_token_expires
    )
    
    LogManager.log_info("auth", "Token de acceso generado correctamente")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_token(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Refresca un token de acceso usando un token de refresco
    """
    # Verificar que el token es de refresco
    if current_user.get("type") != "refresh_token":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido para refresco"
        )
    
    # Crear nuevo token de acceso
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": "api", "type": "access_token"},
        expires_delta=access_token_expires
    )
    
    LogManager.log_info("auth", "Token de acceso refrescado correctamente")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/revoke")
async def revoke_token(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Revoca un token de acceso
    """
    # Obtener el token del encabezado de autorización
    auth_header = current_user.get("auth_header", "")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token no proporcionado"
        )
    
    # Extraer el token
    token = auth_header.split(" ")[1]
    
    # Verificar el token
    try:
        payload = verify_token(token)
    except HTTPException:
        # Si el token ya es inválido, considerarlo como revocado
        return {"message": "Token ya revocado"}
    
    # Agregar a la lista negra
    if blacklist_token(token):
        LogManager.log_info("auth", f"Token revocado correctamente para {payload.get('sub', 'unknown')}")
        return {"message": "Token revocado correctamente"}
    else:
        LogManager.log_error("auth", "Error al revocar token")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al revocar token"
        ) 