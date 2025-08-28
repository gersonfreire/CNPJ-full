from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Servidor
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    API_DEBUG: bool = True
    
    # Segurança
    STATIC_BEARER_TOKEN: str = "seu_token_secreto_aqui"
    
    # Banco de Dados
    DATABASE_URL: str = "sqlite:///H:/dev/rfb/CNPJ-full/output/CNPJ_full.db"
    
    # SSL
    SSL_KEYFILE_PATH: Optional[str] = None
    SSL_CERTFILE_PATH: Optional[str] = None

    class Config:
        env_file = "api/.env"
        env_file_encoding = "utf-8"

settings = Settings()
