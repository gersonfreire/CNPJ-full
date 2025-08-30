import requests
import json
import os
import argparse
from dotenv import load_dotenv

def resolve_config_path(config_file):
    """Resolve o caminho do arquivo de configuração baseado na entrada do usuário."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Se for caminho absoluto, usa diretamente
    if os.path.isabs(config_file):
        return config_file
    
    # Se contém separadores de caminho, trata como caminho relativo
    if os.sep in config_file or '/' in config_file:
        return os.path.join(script_dir, config_file)
    
    # Caso contrário, assume que é só o nome do arquivo na pasta conf
    return os.path.join(script_dir, "conf", config_file)

def parse_arguments():
    """Processa argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Cliente para consultar API de CNPJ com suporte a SQL personalizado",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  %(prog)s
  %(prog)s --config production.env
  %(prog)s --sql "SELECT * FROM empresas LIMIT 10" --page 2
  %(prog)s --url http://localhost:9000 --token abc123
  %(prog)s --config /path/to/config.env --page-size 20
        """
    )
    
    # Arquivo de configuração
    parser.add_argument(
        "--config", "-c",
        default=".env",
        help="Nome do arquivo de configuração (padrão: .env). "
             "Se for só o nome, procura na pasta 'conf'. "
             "Se contiver caminho, usa caminho relativo/absoluto."
    )
    
    # Parâmetros de API
    parser.add_argument(
        "--url", "-u",
        help="URL base da API (substitui API_BASE_URL do .env)"
    )
    
    parser.add_argument(
        "--token", "-t",
        help="Token de autenticação Bearer (substitui BEARER_TOKEN do .env)"
    )
    
    # Parâmetros de consulta
    parser.add_argument(
        "--sql", "-s",
        help="Consulta SQL a ser executada (substitui SQL_QUERY do .env)"
    )
    
    parser.add_argument(
        "--page", "-p",
        type=int,
        help="Número da página (substitui PAGE_NUMBER do .env)"
    )
    
    parser.add_argument(
        "--page-size", "--size",
        type=int,
        help="Itens por página (substitui ITEMS_PER_PAGE do .env)"
    )
    
    return parser.parse_args()

def load_configuration(args):
    """Carrega configurações do arquivo .env e sobrescreve com argumentos da linha de comando."""
    
    # Resolve e carrega o arquivo de configuração
    env_path = resolve_config_path(args.config)
    load_dotenv(env_path)
    
    # Carrega valores do .env com fallbacks padrão
    config = {
        'api_base_url': os.getenv("API_BASE_URL", "http://127.0.0.1:8000"),
        'bearer_token': os.getenv("BEARER_TOKEN", "seu_token_secreto_aqui"),
        'sql_query': os.getenv("SQL_QUERY", "SELECT cnpj, nome_fantasia, capital_social, situacao_cadastral FROM empresas WHERE uf = 'MG' ORDER BY capital_social DESC"),
        'page_number': int(os.getenv("PAGE_NUMBER", "1")),
        'items_per_page': int(os.getenv("ITEMS_PER_PAGE", "5"))
    }
    
    # Sobrescreve com argumentos da linha de comando, se fornecidos
    if args.url:
        config['api_base_url'] = args.url
    if args.token:
        config['bearer_token'] = args.token
    if args.sql:
        config['sql_query'] = args.sql
    if args.page:
        config['page_number'] = args.page
    if args.page_size:
        config['items_per_page'] = args.page_size
    
    return config

def query_api(sql: str, page: int, page_size: int, api_base_url: str, bearer_token: str):
    """Função para fazer a chamada à API e imprimir o resultado."""
    
    endpoint_url = f"{api_base_url}/api/v1/query"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {bearer_token}"
    }
    
    params = {
        "page": page,
        "page_size": page_size
    }
    
    payload = {
        "sql": sql
    }
    
    print(f"--- Executando consulta na página {page} com {page_size} itens ---")
    
    try:
        response = requests.post(endpoint_url, headers=headers, params=params, json=payload)
        
        # Verifica se a requisição foi bem-sucedida
        if response.status_code == 200:
            data = response.json()
            print("Consulta bem-sucedida!")
            print(f"Total de registros: {data['total_count']}")
            print(f"Total de páginas: {data['total_pages']}")
            print(f"Página atual: {data['page']}")
            print("\n--- Dados ---")
            # Imprime os dados de forma legível
            for row in data['data']:
                print(json.dumps(row, indent=2, ensure_ascii=False))
            print("-------------")
            
        else:
            print(f"Erro ao consultar a API. Status: {response.status_code}")
            print(f"Resposta: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão: Não foi possível conectar à API em {api_base_url}.")
        print(f"Detalhe: {e}")

def main():
    """Função principal do script."""
    # Processa argumentos da linha de comando
    args = parse_arguments()
    
    # Carrega configurações
    try:
        config = load_configuration(args)
    except FileNotFoundError:
        env_path = resolve_config_path(args.config)
        print(f"!!! ERRO: Arquivo de configuração não encontrado: {env_path}")
        print(f"Crie o arquivo ou especifique um caminho válido com --config")
        return 1
    except Exception as e:
        print(f"!!! ERRO ao carregar configurações: {e}")
        return 1
    
    # Verifica se o token foi configurado
    if config['bearer_token'] == "":
        print("!!! ATENÇÃO: Configure um token válido no arquivo .env ou use --token")
        print("Exemplo: python example_client.py --token seu_token_real")
        return 1
    
    # Executa a consulta
    query_api(
        sql=config['sql_query'],
        page=config['page_number'],
        page_size=config['items_per_page'],
        api_base_url=config['api_base_url'],
        bearer_token=config['bearer_token']
    )
    
    return 0

if __name__ == "__main__":
    exit(main())
