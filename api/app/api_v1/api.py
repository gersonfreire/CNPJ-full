from fastapi import APIRouter
from app.api_v1.endpoints import query, admin, raw_query

api_router = APIRouter()

# Endpoint administrativo
api_router.include_router(admin.router, tags=["Admin"])

# Endpoint para consulta da rede de relacionamentos (grafo)
api_router.include_router(query.router, prefix="/network", tags=["Rede de Relacionamentos"])

# Endpoint para consultas SQL diretas
api_router.include_router(raw_query.router, tags=["Consulta Direta"])
