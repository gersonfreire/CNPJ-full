import pandas as pd
import networkx as nx
from sqlalchemy.orm import Session
from networkx.readwrite import json_graph

class NetworkBuilderService:
    def __init__(self, db: Session, nivel_max: int = 1):
        self.db = db
        self.nivel_max = nivel_max
        self.G = nx.DiGraph()

    def _get_full_cnpj(self, row):
        return f"{row['cnpj_basico']}{row['cnpj_ordem']}{row['cnpj_dv']}"

    def build_network(self, tipo_consulta: str, valor: str):
        if tipo_consulta == 'cnpj':
            self._explorar_vinculos(1, valor)
        elif tipo_consulta == 'nome_socio':
            self._insere_por_nome(valor)
        elif tipo_consulta == 'cpf':
            cpf_mascarado = '***' + valor[3:9] + '**'
            self._insere_por_cpf(cpf_mascarado)
        return self.G

    def _insere_por_cpf(self, cpf: str):
        query = f"SELECT DISTINCT identificador_socio, cnpj_cpf_socio, nome_socio_razao_social FROM socios WHERE cnpj_cpf_socio = '{cpf}'"
        self._processar_socios_encontrados(query)

    def _insere_por_nome(self, nome: str):
        query = f"SELECT DISTINCT identificador_socio, cnpj_cpf_socio, nome_socio_razao_social FROM socios WHERE nome_socio_razao_social = '{nome.upper()}'"
        self._processar_socios_encontrados(query)

    def _processar_socios_encontrados(self, query: str):
        df_socios = pd.read_sql_query(query, self.db.bind)
        if df_socios.empty:
            return
        for _, socio in df_socios.iterrows():
            tipo_socio = int(socio['identificador_socio'])
            id_socio = socio['cnpj_cpf_socio']
            nome_socio = socio['nome_socio_razao_social']
            pessoa_id = id_socio if tipo_socio == 1 else (id_socio, nome_socio)
            self._explorar_vinculos(tipo_socio, pessoa_id)

    def _explorar_vinculos(self, tipo_pessoa, id_pessoa, nivel=0, origem=None):
        if nivel > self.nivel_max:
            return
        id_node = id_pessoa if tipo_pessoa == 1 else id_pessoa[0] + id_pessoa[1]
        if id_node in self.G and self.G.nodes[id_node].get('nivel', self.nivel_max + 1) <= nivel:
            return
        
        if id_node not in self.G:
            self.G.add_node(id_node, nivel=nivel, tipo_pessoa=tipo_pessoa)
        else:
            self.G.nodes[id_node]['nivel'] = nivel

        if tipo_pessoa == 1:
            self._processar_pj(id_node, nivel)
        else:
            self._processar_pf(id_node, id_pessoa, nivel)

    def _processar_pj(self, cnpj, nivel):
        cnpj_basico = cnpj[:8]
        query_socios = f"SELECT * FROM socios WHERE cnpj_basico = '{cnpj_basico}'"
        df_socios = pd.read_sql_query(query_socios, self.db.bind)
        for _, socio in df_socios.iterrows():
            self._adicionar_vinculo_socio(socio, cnpj, nivel)
        self._buscar_participacoes_societarias(1, cnpj, nivel)

    def _processar_pf(self, id_node, id_pessoa, nivel):
        cpf, nome = id_pessoa
        self.G.nodes[id_node].update({'nome': nome, 'cpf': cpf})
        self._buscar_participacoes_societarias(2, id_pessoa, nivel)

    def _buscar_participacoes_societarias(self, tipo_pessoa, id_pessoa, nivel):
        source_node = id_pessoa if tipo_pessoa == 1 else id_pessoa[0] + id_pessoa[1]
        if tipo_pessoa == 1:
            query = f"SELECT * FROM socios WHERE cnpj_cpf_socio = '{id_pessoa}'"
        else:
            cpf, nome = id_pessoa
            query = f"SELECT * FROM socios WHERE cnpj_cpf_socio = '{cpf}' AND nome_socio_razao_social = '{nome}'"
        df_participacoes = pd.read_sql_query(query, self.db.bind)
        for _, participacao in df_participacoes.iterrows():
            cnpj_basico = participacao['cnpj_basico']
            query_matriz = f"SELECT * FROM estabelecimentos WHERE cnpj_basico = '{cnpj_basico}' AND identificador_matriz_filial = 1"
            df_matriz = pd.read_sql_query(query_matriz, self.db.bind)
            if not df_matriz.empty:
                cnpj_matriz = self._get_full_cnpj(df_matriz.iloc[0])
                self._explorar_vinculos(1, cnpj_matriz, nivel + 1, origem=id_pessoa)
                self.G.add_edge(source_node, cnpj_matriz, tipo='socio', **participacao.to_dict())

    def _adicionar_vinculo_socio(self, socio, cnpj_empresa, nivel):
        tipo_socio = int(socio['identificador_socio'])
        id_socio_num = socio['cnpj_cpf_socio']
        nome_socio = socio['nome_socio_razao_social']
        id_socio_node = id_socio_num if tipo_socio == 1 else id_socio_num + nome_socio
        
        self._explorar_vinculos(tipo_socio, id_socio_num if tipo_socio == 1 else (id_socio_num, nome_socio), nivel + 1, origem=cnpj_empresa)
        self.G.add_edge(id_socio_node, cnpj_empresa, tipo='socio', **socio.to_dict())
