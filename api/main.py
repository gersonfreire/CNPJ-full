import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api_v1.api import api_router

app = FastAPI(
    title="API de Consulta de Rede CNPJ",
    description="API para explorar a rede de relacionamentos de empresas e sócios da base de dados da Receita Federal.",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/", include_in_schema=False)
def read_root():
    return {"message": "Bem-vindo à API de Consulta CNPJ. Acesse /docs para a documentação interativa."}

if __name__ == "__main__":
    ssl_params = {}
    if settings.SSL_KEYFILE_PATH and settings.SSL_CERTFILE_PATH:
        ssl_params["ssl_keyfile"] = settings.SSL_KEYFILE_PATH
        ssl_params["ssl_certfile"] = settings.SSL_CERTFILE_PATH
        print(f"INFO:     Rodando em HTTPS na porta {settings.API_PORT}")
    else:
        print("INFO:     Certificados SSL não encontrados. Rodando em HTTP.")

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        debug=settings.API_DEBUG,
        **ssl_params
    )
