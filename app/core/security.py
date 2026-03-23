from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from app.core.config import settings
from app.core.logging import LogManager
import hashlib
import time

# Configuración de seguridad
api_key_header = APIKeyHeader(name="X-API-Key")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verifica la API key proporcionada
    """
    if api_key != settings.API_KEY:
        LogManager.log_error("security", f"API key inválida: {api_key[:8]}...")
        raise HTTPException(
            status_code=401,
            detail="API key inválida"
        )
    return api_key

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña coincide con el hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Genera un hash de la contraseña."""
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT con los datos proporcionados.
    
    Args:
        data: Datos a incluir en el token
        expires_delta: Tiempo de expiración del token
        
    Returns:
        Token JWT firmado
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    return encoded_jwt

def verify_token(token: str) -> Dict[str, Any]:
    """
    Verifica un token JWT y devuelve los datos decodificados.
    
    Args:
        token: Token JWT a verificar
        
    Returns:
        Datos decodificados del token
        
    Raises:
        HTTPException: Si el token es inválido o ha expirado
    """
    try:
        # Verificar si el token está en la lista negra
        if is_token_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token ha sido revocado",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Decodificar el token con opciones adicionales
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM],
            options={
                "verify_iss": True,
                "verify_aud": True,
                "verify_iat": True,
                "verify_nbf": True,
                "verify_exp": True
            }
        )
        
        # Verificar emisor
        if payload.get("iss") != settings.JWT_ISSUER:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Emisor de token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Verificar audiencia
        if settings.JWT_AUDIENCE and payload.get("aud") != settings.JWT_AUDIENCE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Audiencia de token inválida",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token ha expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError as e:
        LogManager.log_error("security", f"Error de validación JWT: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudo validar el token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(token: str = Depends(verify_api_key)) -> dict:
    """
    Obtiene el usuario actual basado en el token
    """
    return {"api_key": token}

def validate_api_key(api_key: str, expected_key: str) -> bool:
    """Valida una clave API."""
    return api_key == expected_key

def get_brave_api_key() -> str:
    """Obtiene la clave API de Brave."""
    return settings.BRAVE_API_KEY

def get_anthropic_api_key() -> str:
    """Obtiene la clave API de Anthropic."""
    return settings.ANTHROPIC_API_KEY

# Middleware para validar claves API
async def validate_api_keys(request: Dict[str, Any]) -> bool:
    """Valida las claves API en la solicitud."""
    brave_key = request.get("brave_api_key")
    anthropic_key = request.get("anthropic_api_key")
    
    if brave_key and not validate_api_key(brave_key, get_brave_api_key()):
        return False
    
    if anthropic_key and not validate_api_key(anthropic_key, get_anthropic_api_key()):
        return False
    
    return True

def is_token_blacklisted(token: str) -> bool:
    """
    Verifica si un token está en la lista negra.
    
    Args:
        token: Token JWT a verificar
        
    Returns:
        True si el token está en la lista negra, False en caso contrario
    """
    try:
        # Obtener el hash del token para usar como clave
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Verificar en Redis si el token está en la lista negra
        from app.core.cache import cache
        return cache.get(f"blacklist:{token_hash}") is not None
    except Exception as e:
        LogManager.log_error("security", f"Error al verificar lista negra: {str(e)}")
        return False

def blacklist_token(token: str, expires_in: Optional[int] = None) -> bool:
    """
    Agrega un token a la lista negra.
    
    Args:
        token: Token JWT a agregar a la lista negra
        expires_in: Tiempo en segundos para mantener el token en la lista negra
        
    Returns:
        True si se agregó correctamente, False en caso contrario
    """
    try:
        # Obtener el hash del token para usar como clave
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Decodificar el token para obtener su tiempo de expiración
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_signature": False}
        )
        
        # Calcular el tiempo de expiración del token
        exp = payload.get("exp", 0)
        now = int(time.time())
        ttl = exp - now if exp > now else 3600  # 1 hora por defecto
        
        # Usar el tiempo de expiración proporcionado si está disponible
        if expires_in is not None:
            ttl = expires_in
            
        # Agregar a la lista negra en Redis
        from app.core.cache import cache
        return cache.set(f"blacklist:{token_hash}", True, expire=ttl)
    except Exception as e:
        LogManager.log_error("security", f"Error al agregar token a lista negra: {str(e)}")
        return False 