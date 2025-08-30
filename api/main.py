import typer
import os
import sys
import uvicorn
from colorama import just_fix_windows_console
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Resolve paths and ensure imports work when running this file directly
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(THIS_DIR)

# Make the project importable as a package root (so 'api' is resolvable)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Also include the api/ folder to allow relative imports if needed
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

# Import get_settings here, but don't call it yet.
from app.core.config import get_settings

# Import api_router here. Its dependencies (get_db, get_current_user)
# will correctly use get_settings() when they are called.
from app.api_v1.api import api_router

# Create the FastAPI app instance globally.
# Its configuration (title, description, etc.) does not depend on settings.
app = FastAPI(
    title="API de Consulta de Rede CNPJ",
    description="API para explorar a rede de relacionamentos de empresas e sócios da base de dados da Receita Federal.",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json"
)

# Fix Windows console to render ANSI escape sequences correctly
just_fix_windows_console()

# Middlewares - these do not depend on settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers - these are included globally.
# Their dependencies will use get_settings() when invoked.
app.include_router(api_router, prefix="/api/v1")

@app.get("/", include_in_schema=False)
def read_root():
    return {"message": "Bem-vindo à API de Consulta CNPJ. Acesse /docs para a documentação interativa."}


# --- CLI with Typer ---
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
    """Starts the FastAPI API server using Uvicorn."""

    # Set the ENV_FILE environment variable.
    # This must happen BEFORE get_settings() is called for the first time.
    if env_file:
        os.environ["ENV_FILE"] = env_file
        typer.echo(f"INFO:     Usando arquivo de configuração customizado: {env_file}")
    else:
        typer.echo("INFO:     Usando arquivo de configuração padrão.")

    # Ensure the reloader subprocess inherits PYTHONPATH so it can import 'api.main:app'
    existing = os.environ.get("PYTHONPATH", "")
    if PROJECT_ROOT not in existing.split(os.pathsep):
        os.environ["PYTHONPATH"] = PROJECT_ROOT + (os.pathsep + existing if existing else "")

    # Get the settings. This will load them from the .env file (if specified)
    # and cache them for subsequent calls.
    settings = get_settings()

    # Prepare Uvicorn arguments
    uvicorn_args = {
        "host": settings.API_HOST,
        "port": settings.API_PORT,
        "reload": settings.API_RELOAD,
    }

    if settings.SSL_KEYFILE_PATH and settings.SSL_CERTFILE_PATH:
        uvicorn_args["ssl_keyfile"] = settings.SSL_KEYFILE_PATH
        uvicorn_args["ssl_certfile"] = settings.SSL_CERTFILE_PATH
        typer.echo(f"INFO:     Rodando em HTTPS na porta {settings.API_PORT}")
    else:
        typer.echo(f"INFO:     Rodando em HTTP na porta {settings.API_PORT}")

    # Run Uvicorn. Prefer an import string for hot reload; fallback to object if needed.
    try:
        uvicorn.run("api.main:app", **uvicorn_args)
    except ModuleNotFoundError:
        # Fallback for environments where import string resolution fails
        uvicorn.run(app, **uvicorn_args)

if __name__ == "__main__":
    cli()
