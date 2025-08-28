# -*- encoding: utf-8 -*-
import os
import glob
import sys
import datetime
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# --- CONFIGURACOES GERAIS ---

CHUNKSIZE = 250000
ENCODING = 'latin1' # Encoding comumente usado em dados governamentais brasileiros

# --- DEFINICOES DE TABELAS E SCHEMAS ---

# Nomes das tabelas
EMPRESAS = 'empresas'
ESTABELECIMENTOS = 'estabelecimentos'
SOCIOS = 'socios'
SIMPLES = 'simples'
CNAES_SECUNDARIOS = 'cnaes_secundarios'

# Definição de colunas
EMPRESAS_COLS = ['cnpj_basico', 'razao_social', 'natureza_juridica', 'qualificacao_responsavel', 'capital_social', 'porte_empresa', 'ente_federativo_responsavel']
ESTABELECIMENTOS_COLS = ['cnpj_basico', 'cnpj_ordem', 'cnpj_dv', 'identificador_matriz_filial', 'nome_fantasia', 'situacao_cadastral', 'data_situacao_cadastral', 'motivo_situacao_cadastral', 'nome_cidade_exterior', 'pais', 'data_inicio_atividade', 'cnae_fiscal_principal', 'cnae_fiscal_secundaria', 'tipo_logradouro', 'logradouro', 'numero', 'complemento', 'bairro', 'cep', 'uf', 'municipio', 'ddd_1', 'telefone_1', 'ddd_2', 'telefone_2', 'ddd_fax', 'fax', 'email', 'situacao_especial', 'data_situacao_especial']
SOCIOS_COLS = ['cnpj_basico', 'identificador_socio', 'nome_socio_razao_social', 'cnpj_cpf_socio', 'qualificacao_socio', 'data_entrada_sociedade', 'pais', 'representante_legal', 'nome_representante', 'qualificacao_representante_legal', 'faixa_etaria']
SIMPLES_COLS = ['cnpj_basico', 'opcao_pelo_simples', 'data_opcao_simples', 'data_exclusao_simples', 'opcao_pelo_mei', 'data_opcao_mei', 'data_exclusao_mei']

# Dtypes para colunas específicas
EMPRESAS_DTYPES = {'capital_social': 'float64'}

# Mapeamento de prefixos de arquivo para configurações da tabela
FILE_CONFIG = {
    'Empresas': {
        'table_name': EMPRESAS,
        'cols': EMPRESAS_COLS,
        'dtypes': {},
        'special_handler': null
    },
    'Estabelecimentos': {
        'table_name': ESTABELECIMENTOS,
        'cols': ESTABELECIMENTOS_COLS,
        'dtypes': {},
        'special_handler': 'handle_cnaes'
    },
    'Socios': {
        'table_name': SOCIOS,
        'cols': SOCIOS_COLS,
        'dtypes': {},
        'special_handler': null
    },
    'Simples': {
        'table_name': SIMPLES,
        'cols': SIMPLES_COLS,
        'dtypes': {},
        'special_handler': null
    }
}

# --- FUNCOES DE PROCESSAMENTO ---

def handle_cnaes(chunk, db_engine, if_exists_mode):
    cnaes_sec = chunk[['cnpj_basico', 'cnpj_ordem', 'cnpj_dv', 'cnae_fiscal_secundaria']].copy()
    cnaes_sec.dropna(subset=['cnae_fiscal_secundaria'], inplace=True)

    if cnaes_sec.empty:
        return 0

    cnaes_sec['cnpj'] = cnaes_sec['cnpj_basico'].astype(str) + cnaes_sec['cnpj_ordem'].astype(str) + cnaes_sec['cnpj_dv'].astype(str)
    cnaes_sec = cnaes_sec.assign(cnae=cnaes_sec['cnae_fiscal_secundaria'].str.split(',')).explode('cnae')
    
    cnaes_df = cnaes_sec[['cnpj', 'cnae']].copy()
    cnaes_df['cnae'] = cnaes_df['cnae'].str.strip()
    cnaes_df.dropna(subset=['cnae'], inplace=True)
    cnaes_df = cnaes_df[cnaes_df['cnae'] != '']

    if not cnaes_df.empty:
        num_records = len(cnaes_df)
        cnaes_df.to_sql(CNAES_SECUNDARIOS, db_engine, if_exists=if_exists_mode, index=False)
        return num_records
    
    return 0

def process_zip_files(files, config, db_engine):
    table_name = config['table_name']
    columns = config['cols']
    dtypes = config['dtypes']
    handler_func_name = config['special_handler']

    total_records_table = 0
    total_records_handler = 0

    print(f'Iniciando processamento para a tabela: {table_name}')
    
    if_exists_mode = 'replace'
    cnaes_if_exists_mode = 'replace'

    for filepath in files:
        print(f'  Lendo arquivo: {os.path.basename(filepath)}')
        records_in_file = 0
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
                chunk_rows = len(chunk)
                records_in_file += chunk_rows
                total_records_table += chunk_rows
                
                print(f'    Registros lidos do arquivo: {records_in_file:,} | Total na tabela: {total_records_table:,}', end='\r')

                if handler_func_name:
                    records_written_handler = globals()[handler_func_name](chunk, db_engine, cnaes_if_exists_mode)
                    total_records_handler += records_written_handler
                    cnaes_if_exists_mode = 'append'

                for col, dtype in dtypes.items():
                    if col in chunk.columns:
                        chunk[col] = pd.to_numeric(chunk[col].str.replace(',', '.'), errors='coerce').astype(dtype)

                chunk.to_sql(table_name, db_engine, if_exists=if_exists_mode, index=False)
                
                if_exists_mode = 'append'
            
            print(f'    Arquivo {os.path.basename(filepath)} concluído. {records_in_file:,} registros processados.{" " * 20}')

        except Exception as e:
            print(f'\nERRO ao processar o arquivo {filepath}: {e}')
            
    print(f'Processamento finalizado para a tabela: {table_name}')
    print(f'  -> Total de registros gravados: {total_records_table:,}')
    if handler_func_name:
        print(f'  -> Total de registros de CNAE secundário gravados: {total_records_handler:,}')
    print('')

def cnpj_index(db_engine):
    """Cria índices no banco de dados para otimizar as consultas."""
    INDICES = [
        ('empresas_cnpj_basico', EMPRESAS, 'cnpj_basico'),
        ('estabelecimentos_cnpj', ESTABELECIMENTOS, 'cnpj_basico, cnpj_ordem, cnpj_dv'),
        ('socios_cnpj_basico', SOCIOS, 'cnpj_basico'),
        ('socios_cpf_cnpj', SOCIOS, 'cnpj_cpf_socio'),
        ('cnaes_cnpj', CNAES_SECUNDARIOS, 'cnpj')
    ]
    PREFIXO_INDICE = 'ix_'

    print(u'Criando índices...\nEssa operacao pode levar vários minutos.')
    
    with db_engine.connect() as connection:
        for indice in INDICES:
            nome_indice = PREFIXO_INDICE + indice[0]
            nome_tabela = indice[1]
            coluna = indice[2]
            
            try:
                sql_stmt = text(f'CREATE INDEX {nome_indice} ON {nome_tabela} ({coluna});')
                connection.execute(sql_stmt)
                connection.commit()
                print(f'  Índice {nome_indice} criado (ou já existia) na tabela {nome_tabela}.')
            except Exception as e:
                print(f'  AVISO ao criar índice {nome_indice} na tabela {nome_tabela}: {e}')
    
    print(u'Criação de índices concluída.')

def help():
    print('''
Uso: python cnpj_sql.py [<path_input>] [--noindex]

Processa arquivos .zip da Receita Federal e os carrega em um banco de dados
configurado via SQLAlchemy.

A string de conexão do banco de dados deve ser informada na variável DATABASE_URL
em um arquivo .env no mesmo diretório do script.

Se nenhum argumento for fornecido, o seguinte valor padrão será usado:
  - Diretório de entrada: tools/downloads_cnpj

Argumentos:
  <path_input>   : Diretório contendo os arquivos .zip da RFB.
  [--noindex]    : Opcional. Não gera índices no banco de dados ao final.

Exemplo de .env:
  DATABASE_URL="mssql+pyodbc://user:password@server/database?driver=ODBC+Driver+17+for+SQL+Server"

Exemplo de uso:
  python cnpj_sql.py "dados_rfb"
''')

def main():
    load_dotenv()
    
    if len(sys.argv) > 1 and sys.argv[1] in ('-h', '--help'):
        help()
        sys.exit(0)

    input_path = os.path.join('tools', 'downloads_cnpj')
    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        input_path = sys.argv[1]
    else:
        print("Nenhum diretório de entrada fornecido. Usando o padrão: 'tools/downloads_cnpj'")

    gera_index = '--noindex' not in sys.argv

    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERRO: A variável de ambiente DATABASE_URL não está definida.")
        print("Crie um arquivo .env com a string de conexão. Veja --help para um exemplo.")
        sys.exit(-1)

    if not os.path.isdir(input_path):
        print(f'ERRO: O diretório de entrada não foi encontrado: {input_path}')
        sys.exit(-1)

    print(f'Iniciando processamento em {datetime.datetime.now()}')
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as connection:
            print("Conexão com o banco de dados estabelecida com sucesso.")
    except Exception as e:
        print(f"ERRO: Não foi possível conectar ao banco de dados: {e}")
        sys.exit(-1)

    all_zip_files = glob.glob(os.path.join(input_path, '*.zip'))
    if not all_zip_files:
        print(f'ERRO: Nenhum arquivo .zip encontrado em {input_path}')
        sys.exit(-1)

    for file_prefix, config in FILE_CONFIG.items():
        files_to_process = [f for f in all_zip_files if os.path.basename(f).startswith(file_prefix)]
        files_to_process.sort()

        if files_to_process:
            process_zip_files(files_to_process, config, engine)
        else:
            print(f'Nenhum arquivo encontrado para o prefixo: {file_prefix}. Pulando.')

    print('Processamento de dados concluído.')

    if gera_index:
        cnpj_index(engine)
        
    print(f'Processamento concluído em {datetime.datetime.now()}')

if __name__ == "__main__":
    main()
