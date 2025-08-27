# -*- encoding: utf-8 -*-
import os
import glob
import sys
import datetime
import sqlite3
import pandas as pd

# --- CONFIGURACOES GERAIS ---

NOME_ARQUIVO_SQLITE = 'CNPJ_full.db'
CHUNKSIZE = 250000
ENCODING = 'latin1' # Encoding comumente usado em dados governamentais brasileiros

# --- DEFINICOES DE TABELAS E SCHEMAS ---

# Nomes das tabelas
EMPRESAS = 'empresas'
ESTABELECIMENTOS = 'estabelecimentos'
SOCIOS = 'socios'
SIMPLES = 'simples'
CNAES_SECUNDARIOS = 'cnaes_secundarios'

# Definição de colunas baseada no PDF "Novo Layout para os DADOS ABERTOS do CNPJ"
# Nomes em minúsculo para seguir a convenção do script original.
EMPRESAS_COLS = ['cnpj_basico', 'razao_social', 'natureza_juridica', 'qualificacao_responsavel', 'capital_social', 'porte_empresa', 'ente_federativo_responsavel']
ESTABELECIMENTOS_COLS = ['cnpj_basico', 'cnpj_ordem', 'cnpj_dv', 'identificador_matriz_filial', 'nome_fantasia', 'situacao_cadastral', 'data_situacao_cadastral', 'motivo_situacao_cadastral', 'nome_cidade_exterior', 'pais', 'data_inicio_atividade', 'cnae_fiscal_principal', 'cnae_fiscal_secundaria', 'tipo_logradouro', 'logradouro', 'numero', 'complemento', 'bairro', 'cep', 'uf', 'municipio', 'ddd_1', 'telefone_1', 'ddd_2', 'telefone_2', 'ddd_fax', 'fax', 'email', 'situacao_especial', 'data_situacao_especial']
SOCIOS_COLS = ['cnpj_basico', 'identificador_socio', 'nome_socio_razao_social', 'cnpj_cpf_socio', 'qualificacao_socio', 'data_entrada_sociedade', 'pais', 'representante_legal', 'nome_representante', 'qualificacao_representante_legal', 'faixa_etaria']
SIMPLES_COLS = ['cnpj_basico', 'opcao_pelo_simples', 'data_opcao_simples', 'data_exclusao_simples', 'opcao_pelo_mei', 'data_opcao_mei', 'data_exclusao_mei']

# Dtypes para colunas específicas
EMPRESAS_DTYPES = {'capital_social': 'float64'}
# Todos os outros serão lidos como string para evitar erros de tipo em dados sujos.

# Mapeamento de prefixos de arquivo para configurações da tabela
# Adicione outros arquivos como 'Paises', 'Municipios' aqui se necessário
FILE_CONFIG = {
    'Empresas': {
        'table_name': EMPRESAS,
        'cols': EMPRESAS_COLS,
        'dtypes': EMPRESAS_DTYPES,
        'special_handler': None
    },
    'Estabelecimentos': {
        'table_name': ESTABELECIMENTOS,
        'cols': ESTABELECIMENTOS_COLS,
        'dtypes': {},
        'special_handler': 'handle_cnaes' # Função especial para tratar CNAEs secundários
    },
    'Socios': {
        'table_name': SOCIOS,
        'cols': SOCIOS_COLS,
        'dtypes': {},
        'special_handler': None
    },
    'Simples': {
        'table_name': SIMPLES,
        'cols': SIMPLES_COLS,
        'dtypes': {},
        'special_handler': None
    }
}

# --- FUNCOES DE PROCESSAMENTO ---

def handle_cnaes(chunk, db_connection, if_exists_mode):
    """
    Extrai, normaliza e salva os CNAEs secundários de um chunk de estabelecimentos.
    """
    cnaes_sec = chunk[['cnpj_basico', 'cnpj_ordem', 'cnpj_dv', 'cnae_fiscal_secundaria']].copy()
    cnaes_sec.dropna(subset=['cnae_fiscal_secundaria'], inplace=True)

    if cnaes_sec.empty:
        return

    # Monta o CNPJ completo
    cnaes_sec['cnpj'] = cnaes_sec['cnpj_basico'].astype(str) + cnaes_sec['cnpj_ordem'].astype(str) + cnaes_sec['cnpj_dv'].astype(str)
    
    # Separa os CNAEs que vêm em formato de string separada por vírgula
    cnaes_sec = cnaes_sec.assign(cnae=cnaes_sec['cnae_fiscal_secundaria'].str.split(',')).explode('cnae')
    
    # Limpa e seleciona as colunas finais
    cnaes_df = cnaes_sec[['cnpj', 'cnae']].copy()
    cnaes_df['cnae'] = cnaes_df['cnae'].str.strip()
    cnaes_df.dropna(subset=['cnae'], inplace=True)
    cnaes_df = cnaes_df[cnaes_df['cnae'] != '']

    if not cnaes_df.empty:
        cnaes_df.to_sql(CNAES_SECUNDARIOS, db_connection, if_exists=if_exists_mode, index=False)

def process_zip_files(files, config, db_connection, output_type):
    """
    Lê uma lista de arquivos ZIP, processa os CSVs internos em blocos
    e os carrega na tabela SQLite especificada na configuração.
    """
    table_name = config['table_name']
    columns = config['cols']
    dtypes = config['dtypes']
    handler_func_name = config['special_handler']

    print(f'Iniciando processamento para a tabela: {table_name}')
    
    # O primeiro bloco de dados de qualquer arquivo substitui a tabela. Os demais anexam.
    if_exists_mode = 'replace'
    cnaes_if_exists_mode = 'replace'

    for filepath in files:
        print(f'  Lendo arquivo: {os.path.basename(filepath)}')
        try:
            reader = pd.read_csv(
                filepath,
                sep=';',
                header=None,
                names=columns,
                dtype=str,
                encoding=ENCODING,
                chunksize=CHUNKSIZE,
                compression='zip'
            )

            for i, chunk in enumerate(reader):
                print(f'    Processando bloco {i+1}...', end='\r')

                # Aplica o handler especial se houver um
                if handler_func_name:
                    globals()[handler_func_name](chunk, db_connection, cnaes_if_exists_mode)
                    cnaes_if_exists_mode = 'append' # Garante que o handler só use 'replace' uma vez

                # Converte os tipos de dados
                for col, dtype in dtypes.items():
                    if col in chunk.columns:
                        chunk[col] = pd.to_numeric(chunk[col].str.replace(',', '.'), errors='coerce').astype(dtype)

                # Salva no banco de dados
                if output_type == 'sqlite':
                    chunk.to_sql(table_name, db_connection, if_exists=if_exists_mode, index=False)
                
                if_exists_mode = 'append' # Garante que apenas o primeiro bloco substitua a tabela
            
            print(f'    Arquivo {os.path.basename(filepath)} concluído.{" " * 20}')

        except Exception as e:
            print(f'\nERRO ao processar o arquivo {filepath}: {e}')
    print(f'Processamento finalizado para a tabela: {table_name}\n')

def cnpj_index(output_path):
    """Cria índices no banco de dados para otimizar as consultas."""
    # (Esta função foi corrigida na interação anterior para ser mais robusta)
    
    # Índices a serem criados: (nome_indice, tabela, coluna)
    INDICES = [
        ('empresas_cnpj_basico', EMPRESAS, 'cnpj_basico'),
        ('estabelecimentos_cnpj', ESTABELECIMENTOS, 'cnpj_basico, cnpj_ordem, cnpj_dv'),
        ('socios_cnpj_basico', SOCIOS, 'cnpj_basico'),
        ('socios_cpf_cnpj', SOCIOS, 'cnpj_cpf_socio'),
        ('cnaes_cnpj', CNAES_SECUNDARIOS, 'cnpj')
    ]
    PREFIXO_INDICE = 'ix_'

    conBD = sqlite3.connect(os.path.join(output_path, NOME_ARQUIVO_SQLITE))
    print(u'Criando índices...\nEssa operacao pode levar vários minutos.')
    cursorBD = conBD.cursor()

    cursorBD.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursorBD.fetchall()}

    for indice in INDICES:
        nome_indice = PREFIXO_INDICE + indice[0]
        nome_tabela = indice[1]
        coluna = indice[2]

        if nome_tabela in tables:
            try:
                sql_stmt = f'CREATE INDEX IF NOT EXISTS {nome_indice} ON {nome_tabela} ({coluna});'
                cursorBD.execute(sql_stmt)
                print(f'  Índice {nome_indice} criado na tabela {nome_tabela}.')
            except Exception as e:
                print(f'  ERRO ao criar índice {nome_indice} na tabela {nome_tabela}: {e}')
        else:
            print(f'  Aviso: Tabela "{nome_tabela}" não encontrada. O índice {nome_indice} não será criado.')

    print(u'Criação de índices concluída.')
    conBD.close()

def help():
    print('''
Uso: python cnpj.py <path_input> <output:sqlite|csv> <path_output> [--noindex]
O script agora processa arquivos .zip (Empresas*.zip, Socios*.zip, etc.) 
encontrados no diretório de entrada, assumindo que eles contêm arquivos CSV
delimitados por ponto e vírgula, conforme o novo layout da Receita Federal.

Argumentos:
  <path_input>   : Diretório contendo os arquivos .zip da RFB.
  <output:sqlite>: Formato de saída. Atualmente, apenas 'sqlite' é suportado.
  <path_output>  : Diretório onde o banco de dados SQLite será salvo.
  [--noindex]    : Opcional. Não gera índices no banco de dados ao final.

Exemplo:
  python cnpj.py "dados_rfb" sqlite "output"
''')

def main():
    # --- Leitura dos Argumentos ---
    if len(sys.argv) < 4:
        help()
        sys.exit(-1)

    input_path = sys.argv[1]
    tipo_output = sys.argv[2]
    output_path = sys.argv[3]
    gera_index = '--noindex' not in sys.argv

    if tipo_output != 'sqlite':
        print("ERRO: Apenas o tipo de output 'sqlite' é suportado nesta versão.")
        help()
        sys.exit(-1)

    if not os.path.isdir(input_path):
        print(f'ERRO: O diretório de entrada não foi encontrado: {input_path}')
        sys.exit(-1)

    # --- Lógica Principal ---
    print(f'Iniciando processamento em {datetime.datetime.now()}')
    
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    db_path = os.path.join(output_path, NOME_ARQUIVO_SQLITE)
    # Remove o banco de dados antigo para garantir uma carga limpa
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f'Banco de dados antigo removido: {db_path}')

    conBD = sqlite3.connect(db_path)

    # Encontra todos os arquivos .zip no diretório de entrada
    all_zip_files = glob.glob(os.path.join(input_path, '*.zip'))
    if not all_zip_files:
        print(f'ERRO: Nenhum arquivo .zip encontrado em {input_path}')
        sys.exit(-1)

    # Itera sobre a configuração e processa cada tipo de arquivo
    for file_prefix, config in FILE_CONFIG.items():
        files_to_process = [f for f in all_zip_files if os.path.basename(f).startswith(file_prefix)]
        files_to_process.sort()

        if files_to_process:
            process_zip_files(files_to_process, config, conBD, tipo_output)
        else:
            print(f'Nenhum arquivo encontrado para o prefixo: {file_prefix}. Pulando.')

    conBD.close()
    print('Processamento de dados concluído.')

    if gera_index and tipo_output == 'sqlite':
        cnpj_index(output_path)
        
    print(f'Processamento concluído em {datetime.datetime.now()}')

if __name__ == "__main__":
    main()