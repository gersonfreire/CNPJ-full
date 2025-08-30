from pydantic_settings import BaseSettings
from typing import Optional
import os
from functools import lru_cache

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
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    """
    Cria e retorna uma instância de Settings.
    A primeira chamada irá ler a variável de ambiente ENV_FILE para carregar
    o arquivo .env correto. As chamadas subsequentes retornarão a instância em cache.
    Se ENV_FILE não for definido, tentará carregar de 'api/.env' (relativo ao diretório da API).
    """
    env_file_from_env_var = os.getenv("ENV_FILE")
    
    if env_file_from_env_var and os.path.exists(env_file_from_env_var):
        return Settings(_env_file=env_file_from_env_var)
    else:
        # Se ENV_FILE não foi definido ou o arquivo não existe, tenta o padrão api/.env
        # Obtém o diretório do arquivo atual (config.py)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Sobe dois níveis para chegar ao diretório 'api'
        api_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
        default_api_env_path = os.path.join(api_dir, '.env')
        
        if os.path.exists(default_api_env_path):
            return Settings(_env_file=default_api_env_path)
        else:
            # Fallback para o comportamento padrão do pydantic-settings
            # (procura por .env no CWD ou carrega de variáveis de ambiente)
            return Settings()
