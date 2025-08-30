import requests
import json

# --- Configurações ---
# Endereço base da sua API (certifique-se de que o servidor está rodando)
API_BASE_URL = "http://127.0.0.1:8000"

# Cole aqui o mesmo token que você definiu no seu arquivo api/.env
BEARER_TOKEN = "seu_token_secreto_aqui" 

# --- Parâmetros da Consulta ---
# A consulta SQL que você deseja executar
sql_query = "SELECT cnpj, nome_fantasia, capital_social, situacao_cadastral FROM empresas WHERE uf = 'MG' ORDER BY capital_social DESC"

# Parâmetros de paginação
page_number = 1
items_per_page = 5

def query_api(sql: str, page: int, page_size: int):
    """Função para fazer a chamada à API e imprimir o resultado."""
    
    endpoint_url = f"{API_BASE_URL}/api/v1/query"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BEARER_TOKEN}"
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
        print(f"Erro de conexão: Não foi possível conectar à API em {API_BASE_URL}.")
        print(f"Detalhe: {e}")

if __name__ == "__main__":
    if BEARER_TOKEN == "seu_token_secreto_aqui":
        print("!!! ATENÇÃO: Por favor, edite o arquivo 'example_client.py' e substitua 'seu_token_secreto_aqui' pelo seu token real. !!!")
    else:
        query_api(sql=sql_query, page=page_number, items_per_page=items_per_page)
