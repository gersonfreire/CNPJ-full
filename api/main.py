import typer
import os
import subprocess
import sys

# Adiciona o diretório do script ao sys.path para resolver ModuleNotFoundError
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# As configurações são importadas DEPOIS que a variável de ambiente é potencialmente definida.
from app.core.config import settings
from app.api_v1.api import api_router

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
        None, 
        "--env", 
        "-e", 
        help="Caminho para o arquivo .env a ser usado."
    )
):
    """Inicia o servidor da API FastAPI usando Uvicorn."""
    
    # Define a variável de ambiente que será lida pelo módulo de configuração.
    # Isso precisa acontecer ANTES que qualquer módulo de 'app' seja importado.
    if env_file:
        os.environ["ENV_FILE"] = env_file
        typer.echo(f"INFO:     Usando arquivo de configuração customizado: {env_file}")
    else:
        typer.echo("INFO:     Usando arquivo de configuração padrão.")

    # Constrói o comando para executar o Uvicorn
    # Usar o import string "api.main:app" é crucial para o reload funcionar.
    command = [
        "uvicorn",
        "api.main:app",
        f"--host={settings.API_HOST}",
        f"--port={settings.API_PORT}"
    ]
    if settings.API_RELOAD:
        command.append("--reload")

    # Adiciona parâmetros SSL se definidos
    if settings.SSL_KEYFILE_PATH and settings.SSL_CERTFILE_PATH:
        command.append(f"--ssl-keyfile={settings.SSL_KEYFILE_PATH}")
        command.append(f"--ssl-certfile={settings.SSL_CERTFILE_PATH}")
        typer.echo(f"INFO:     Rodando em HTTPS na porta {settings.API_PORT}")
    else:
        typer.echo(f"INFO:     Rodando em HTTP na porta {settings.API_PORT}")

    # Executa o comando Uvicorn
    subprocess.run(command)

if __name__ == "__main__":
    cli()
