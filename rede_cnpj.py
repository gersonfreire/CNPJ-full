import pandas as pd
import networkx as nx
from networkx.readwrite import json_graph

class RedeCNPJ:
    """
    Classe para construção e manipulação de uma rede de CNPJs (empresas e sócios)
    a partir de um banco de dados gerado pelo script cnpj.py.
    """
    def __init__(self, conBD, nivel_max=1, qualificacoes='TODAS'):
        self.__conBD = conBD
        self.__nivel_max = nivel_max
        self.__qualificacoes = qualificacoes
        self.G = nx.DiGraph()

    def _get_full_cnpj(self, row):
        """Monta o CNPJ completo a partir das partes."""
        return f"{row['cnpj_basico']}{row['cnpj_ordem']}{row['cnpj_dv']}"

    def insere_pessoa(self, tipo_pessoa, id_pessoa):
        """Inicia a busca na rede a partir de uma pessoa (física ou jurídica)."""
        self._explorar_vinculos(tipo_pessoa=tipo_pessoa, id_pessoa=id_pessoa)

    def insere_com_cpf_ou_nome(self, cpf='', nome=''):
        """Busca sócios por CPF ou nome e os adiciona à rede."""
        if not cpf and not nome:
            return

        query = "SELECT DISTINCT identificador_socio, cnpj_cpf_socio, nome_socio_razao_social FROM socios WHERE"
        if cpf:
            query += f" cnpj_cpf_socio = '{cpf}'"
        else:
            query += f" nome_socio_razao_social = '{nome}'"
        
        df_socios = pd.read_sql_query(query, self.__conBD)
        if df_socios.empty:
            print(f'Nenhum sócio encontrado com os dados informados (CPF: {cpf}, Nome: {nome})')
            return

        for _, socio in df_socios.iterrows():
            id_socio = socio['cnpj_cpf_socio']
            nome_socio = socio['nome_socio_razao_social']
            tipo_socio = int(socio['identificador_socio'])
            
            pessoa_id = id_socio if tipo_socio == 1 else (id_socio, nome_socio)
            self._explorar_vinculos(tipo_pessoa=tipo_socio, id_pessoa=pessoa_id)

    def _explorar_vinculos(self, tipo_pessoa, id_pessoa, nivel=0, origem=None):
        """Função recursiva para explorar os relacionamentos da rede."""
        if nivel > self.__nivel_max:
            return

        id_node = id_pessoa if tipo_pessoa == 1 else id_pessoa[0] + id_pessoa[1]

        if id_node in self.G and self.G.nodes[id_node]['nivel'] <= nivel:
            return

        # Adiciona ou atualiza o nó no grafo
        if id_node not in self.G:
            self.G.add_node(id_node, nivel=nivel, tipo_pessoa=tipo_pessoa)
        else:
            self.G.nodes[id_node]['nivel'] = nivel

        if tipo_pessoa == 1: # Pessoa Jurídica
            self._processar_pj(id_node, nivel, origem)
        else: # Pessoa Física
            self._processar_pf(id_node, id_pessoa, nivel, origem)

    def _processar_pj(self, cnpj, nivel, origem):
        """Processa os vínculos de uma Pessoa Jurídica."""
        # Adiciona dados do estabelecimento
        cnpj_basico = cnpj[:8]
        cnpj_ordem = cnpj[8:12]
        cnpj_dv = cnpj[12:]
        query_estabelecimento = f"SELECT * FROM estabelecimentos WHERE cnpj_basico = '{cnpj_basico}' AND cnpj_ordem = '{cnpj_ordem}' AND cnpj_dv = '{cnpj_dv}'"
        df_est = pd.read_sql_query(query_estabelecimento, self.__conBD)

        if df_est.empty:
            print(f"Dados do estabelecimento não encontrados para o CNPJ: {cnpj}")
            return

        est_data = df_est.iloc[0].to_dict()
        self.G.nodes[cnpj].update(est_data)
        self.G.nodes[cnpj]['nome'] = est_data.get('nome_fantasia') or est_data.get('razao_social', 'N/A')

        # Busca sócios da empresa
        query_socios = f"SELECT * FROM socios WHERE cnpj_basico = '{cnpj_basico}'"
        df_socios = pd.read_sql_query(query_socios, self.__conBD)
        for _, socio in df_socios.iterrows():
            self._adicionar_vinculo_socio(socio, cnpj, nivel, origem)

        # Busca empresas em que esta PJ é sócia
        self._buscar_participacoes_societarias(1, cnpj, nivel, origem)

    def _processar_pf(self, id_node, id_pessoa, nivel, origem):
        """Processa os vínculos de uma Pessoa Física."""
        cpf, nome = id_pessoa
        self.G.nodes[id_node].update({'nome': nome, 'cpf': cpf})
        self._buscar_participacoes_societarias(2, id_pessoa, nivel, origem)

    def _buscar_participacoes_societarias(self, tipo_pessoa, id_pessoa, nivel, origem):
        """Busca empresas onde a pessoa (física ou jurídica) é sócia."""
        if tipo_pessoa == 1: # PJ
            query = f"SELECT * FROM socios WHERE cnpj_cpf_socio = '{id_pessoa}'"
        else: # PF
            cpf, nome = id_pessoa
            query = f"SELECT * FROM socios WHERE cnpj_cpf_socio = '{cpf}' AND nome_socio_razao_social = '{nome}'"

        df_participacoes = pd.read_sql_query(query, self.__conBD)
        for _, participacao in df_participacoes.iterrows():
            cnpj_basico_empresa = participacao['cnpj_basico']
            # Precisamos encontrar o CNPJ completo da matriz para adicionar à rede
            query_matriz = f"SELECT * FROM estabelecimentos WHERE cnpj_basico = '{cnpj_basico_empresa}' AND identificador_matriz_filial = 1"
            df_matriz = pd.read_sql_query(query_matriz, self.__conBD)
            if not df_matriz.empty:
                cnpj_matriz = self._get_full_cnpj(df_matriz.iloc[0])
                if cnpj_matriz != origem:
                    self._explorar_vinculos(1, cnpj_matriz, nivel + 1, origem=id_pessoa)
                    self.G.add_edge(id_node, cnpj_matriz, tipo='socio', **participacao.to_dict())

    def _adicionar_vinculo_socio(self, socio, cnpj_empresa, nivel, origem):
        """Adiciona um nó de sócio e o conecta à empresa."""
        tipo_socio = int(socio['identificador_socio'])
        id_socio_num = socio['cnpj_cpf_socio']
        nome_socio = socio['nome_socio_razao_social']

        if tipo_socio == 1: # Sócio PJ
            id_socio_node = id_socio_num
            if id_socio_node != origem:
                self._explorar_vinculos(1, id_socio_node, nivel + 1, origem=cnpj_empresa)
        else: # Sócio PF
            id_socio_node = id_socio_num + nome_socio
            if id_socio_node != origem:
                self._explorar_vinculos(2, (id_socio_num, nome_socio), nivel + 1, origem=cnpj_empresa)
        
        self.G.add_edge(id_socio_node, cnpj_empresa, tipo='socio', **socio.to_dict())

    # --- Métodos de Geração de Output ---
    def dataframe_pessoas(self):
        return pd.DataFrame.from_dict(dict(self.G.nodes(data=True)), orient='index')

    def dataframe_vinculos(self):
        if not self.G.edges():
            return pd.DataFrame()
        edge_data = self.G.edges(data=True)
        return pd.DataFrame([i[2] for i in edge_data], 
                            index=pd.MultiIndex.from_tuples([(i[0], i[1]) for i in edge_data], 
                            names=['source','target']))

    def json(self):
        return json_graph.node_link_data(self.G)

    def gera_graphml(self, path):
        nx.write_graphml(self.G, path)

    def gera_gexf(self, path):
        G_adapt = self.G.copy()
        for node, data in G_adapt.nodes(data=True):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    G_adapt.nodes[node][key] = str(value)
        nx.write_gexf(G_adapt, path)
