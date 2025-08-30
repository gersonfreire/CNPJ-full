from fastapi import APIRouter

router = APIRouter()

@router.get("/status", summary="Verifica a saúde da API", tags=["Admin"])
def get_status():
    """
    Endpoint para verificar se a API está operacional.
    """
    return {"status": "ok"}
