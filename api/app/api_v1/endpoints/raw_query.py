import sqlite3
import math
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Any, Dict

from app.core.config import settings
from app.security.auth import get_current_user

router = APIRouter()

# Modelo para o corpo da requisição
class SQLQuery(BaseModel):
    sql: str = Field(..., description="A consulta SQL a ser executada no banco de dados.")

# Modelo para a resposta paginada
class PaginatedResponse(BaseModel):
    total_count: int = Field(..., description="Número total de registros encontrados para a consulta.")
    total_pages: int = Field(..., description="Número total de páginas.")
    page: int = Field(..., description="Número da página atual.")
    page_size: int = Field(..., description="Número de registros por página.")
    data: List[Dict[str, Any]] = Field(..., description="Os dados da página atual.")

@router.post("/query", 
            response_model=PaginatedResponse, 
            summary="Executa uma consulta SQL paginada no banco de dados", 
            tags=["Consulta Direta"], 
            dependencies=[Depends(get_current_user)])
def execute_query(query: SQLQuery, 
                  page: int = Query(1, ge=1, description="Número da página a ser retornada."), 
                  page_size: int = Query(10, ge=1, le=200, description="Número de registros por página.")):
    """
    Executa uma consulta SQL **diretamente** no banco de dados SQLite e retorna os resultados de forma paginada.

    - **Atenção:** Este endpoint é poderoso e permite a execução de qualquer consulta SQL. O acesso é protegido por token, mas deve ser usado com extremo cuidado.
    - A consulta é executada em modo de leitura. Comandos de escrita (INSERT, UPDATE, DELETE, etc.) não são permitidos.
    """
    clean_sql = query.sql.strip()
    if clean_sql.upper().startswith("SELECT") is False:
        raise HTTPException(status_code=403, detail="Apenas consultas SELECT são permitidas.")
    
    if any(keyword in clean_sql.upper() for keyword in ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE"]):
        raise HTTPException(status_code=403, detail="Operações de escrita não são permitidas.")

    db_path = settings.DATABASE_URL.replace("sqlite:///", "")

    try:
        conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 1. Executar a contagem total de registros
        count_sql = f"SELECT COUNT(*) FROM ({clean_sql}) AS subquery"
        cursor.execute(count_sql)
        total_count = cursor.fetchone()[0]

        if total_count == 0:
            return PaginatedResponse(total_count=0, total_pages=0, page=page, page_size=page_size, data=[])

        total_pages = math.ceil(total_count / page_size)
        if page > total_pages:
            raise HTTPException(status_code=404, detail=f"Página solicitada ({page}) excede o número total de páginas ({total_pages}).")

        # 2. Executar a consulta paginada
        offset = (page - 1) * page_size
        paginated_sql = f"{clean_sql} LIMIT {page_size} OFFSET {offset}"
        cursor.execute(paginated_sql)
        result = cursor.fetchall()
        
        data = [dict(row) for row in result]
        
        return PaginatedResponse(
            total_count=total_count,
            total_pages=total_pages,
            page=page,
            page_size=page_size,
            data=data
        )

    except sqlite3.Error as e:
        raise HTTPException(status_code=400, detail=f"Erro na consulta SQL: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
