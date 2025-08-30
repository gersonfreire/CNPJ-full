from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Servidor
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    API_DEBUG: bool = True
    
    # Segurança
    STATIC_BEARER_TOKEN: str = "seu_token_secreto_aqui"
    
    # Banco de Dados
    DATABASE_URL: str = "sqlite:///./output/CNPJ_full.db"
    
    # SSL
    SSL_KEYFILE_PATH: Optional[str] = None
    SSL_CERTFILE_PATH: Optional[str] = None

    class Config:
        # Lê o caminho do arquivo .env da variável de ambiente 'ENV_FILE'.
        # Se não for definida, usa 'api/.env' como padrão.
        env_file = os.getenv("ENV_FILE", "api/.env")
        env_file_encoding = "utf-8"

# A instância global de configurações é criada aqui, lendo a variável de ambiente.
settings = Settings()
