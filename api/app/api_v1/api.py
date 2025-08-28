from fastapi import APIRouter
from app.api_v1.endpoints import query

api_router = APIRouter()
api_router.include_router(query.router, prefix="/network", tags=["Rede de Relacionamentos"])
