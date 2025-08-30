import uvicorn
import typer
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from functools import lru_cache

from app.core.config import Settings
from app.api_v1.api import api_router

# Dependência para obter as configurações
# Usamos lru_cache para garantir que o arquivo .env seja lido apenas uma vez.
@lru_cache
def get_settings(env_file: str = "api/.env") -> Settings:
    return Settings(_env_file=env_file)

# Criação da aplicação FastAPI
app = FastAPI(
    title="API de Consulta de Rede CNPJ",
    description="API para explorar a rede de relacionamentos de empresas e sócios da base de dados da Receita Federal.",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json"
)

# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Roteadores
app.include_router(api_router, prefix="/api/v1")

@app.get("/", include_in_schema=False)
def read_root():
    return {"message": "Bem-vindo à API de Consulta CNPJ. Acesse /docs para a documentação interativa."}


# --- Interface de Linha de Comando (CLI) com Typer ---
cli = typer.Typer()

@cli.command()
def run(
    env_file: str = typer.Option(
        "api/.env", 
        "--env", 
        "-e", 
        help="Caminho para o arquivo .env a ser usado."
    )
):
    """Inicia o servidor da API FastAPI."""
    
    # Carrega as configurações a partir do arquivo .env especificado
    settings = get_settings(env_file)

    # Sobrescreve a dependência get_settings para usar o arquivo correto
    # Isso garante que todos os endpoints usem as configurações carregadas pela CLI
    app.dependency_overrides[get_settings] = lambda: get_settings(env_file)

    typer.echo(f"INFO:     Usando arquivo de configuração: {env_file}")

    ssl_params = {}
    if settings.SSL_KEYFILE_PATH and settings.SSL_CERTFILE_PATH:
        ssl_params["ssl_keyfile"] = settings.SSL_KEYFILE_PATH
        ssl_params["ssl_certfile"] = settings.SSL_CERTFILE_PATH
        typer.echo(f"INFO:     Rodando em HTTPS na porta {settings.API_PORT}")
    else:
        typer.echo("INFO:     Certificados SSL não encontrados. Rodando em HTTP.")

    uvicorn.run(
        app, # Passa o objeto app diretamente
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        **ssl_params
    )

if __name__ == "__main__":
    cli()
