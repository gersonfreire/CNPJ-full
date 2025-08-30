from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    if not credentials or credentials.scheme != "Bearer" or credentials.credentials != settings.STATIC_BEARER_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou não fornecido.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"user": "authenticated"}
