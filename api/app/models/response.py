from pydantic import BaseModel, Field
from typing import List, Dict, Any

class Node(BaseModel):
    id: str = Field(..., description="Identificador único do nó (CNPJ para PJ, CPF+Nome para PF).")
    attributes: Dict[str, Any] = Field(..., description="Dicionário com os atributos do nó.")

class Edge(BaseModel):
    source: str = Field(..., description="ID do nó de origem do vínculo.")
    target: str = Field(..., description="ID do nó de destino do vínculo.")
    attributes: Dict[str, Any] = Field(..., description="Dicionário com os atributos do vínculo (ex: qualificação do sócio).")

class Graph(BaseModel):
    """Modelo de resposta para a rede de relacionamentos."""
    nodes: List[Node] = Field(..., description="Lista de nós (empresas ou pessoas) na rede.")
    edges: List[Edge] = Field(..., description="Lista de arestas (vínculos) entre os nós.")
