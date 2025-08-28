from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.services.network_service import NetworkBuilderService
from app.models.response import Graph, Node, Edge
from app.security.auth import get_current_user
import networkx as nx

router = APIRouter()

@router.get("/", response_model=Graph, summary="Consulta a rede de relacionamentos", dependencies=[Depends(get_current_user)])
def get_network(
    tipo_consulta: str = Query(..., description="Tipo de consulta a ser realizada.", enum=['cnpj', 'cpf', 'nome_socio']),
    valor: str = Query(..., description="O valor a ser consultado (um CNPJ, CPF ou nome de sócio)."),
    nivel_max: int = Query(1, description="Profundidade máxima da busca na rede de relacionamentos.", ge=0, le=3),
    db: Session = Depends(get_db)
):
    """
    Constrói e retorna uma rede de relacionamentos a partir de um ponto de entrada (CNPJ, CPF ou Nome de Sócio).

    - **cnpj**: Forneça um número de CNPJ (14 dígitos, sem formatação) para iniciar a busca a partir de uma empresa.
    - **cpf**: Forneça um número de CPF (11 dígitos, sem formatação) para buscar todas as participações societárias da pessoa física.
    - **nome_socio**: Forneça o nome completo de um sócio para buscar suas participações.
    
    A profundidade da busca pode ser controlada pelo parâmetro `nivel_max` (0 a 3).
    """
    if tipo_consulta == 'cnpj' and (not valor.isdigit() or len(valor) != 14):
        raise HTTPException(status_code=400, detail="CNPJ inválido. Forneça 14 dígitos numéricos.")
    if tipo_consulta == 'cpf' and (not valor.isdigit() or len(valor) != 11):
        raise HTTPException(status_code=400, detail="CPF inválido. Forneça 11 dígitos numéricos.")

    service = NetworkBuilderService(db=db, nivel_max=nivel_max)
    graph = service.build_network(tipo_consulta=tipo_consulta, valor=valor)

    if not graph.nodes:
        raise HTTPException(status_code=404, detail="Nenhum resultado encontrado para a consulta.")

    nodes = [Node(id=node, attributes=data) for node, data in graph.nodes(data=True)]
    edges = [Edge(source=u, target=v, attributes=data) for u, v, data in graph.edges(data=True)]
    
    return Graph(nodes=nodes, edges=edges)
