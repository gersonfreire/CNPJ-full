# API de Consulta CNPJ

Esta API fornece acesso à base de dados da Receita Federal, permitindo a exploração da rede de relacionamentos entre empresas e sócios, bem como a execução de consultas SQL diretas no banco de dados.

A API é construída com FastAPI e é documentada automaticamente via Swagger UI.

## Pré-requisitos

- Python 3.8+
- Pip (gerenciador de pacotes do Python)

## Configuração

1.  **Clone o Repositório:**
    ```bash
    git clone <URL_DO_REPOSITORIO>
    cd CNPJ-full
    ```

2.  **Crie um Ambiente Virtual:**
    É uma boa prática usar um ambiente virtual para isolar as dependências do projeto.
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # No Windows: .venv\\Scripts\\activate
    ```

3.  **Instale as Dependências:**
    As dependências estão listadas no arquivo `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as Variáveis de Ambiente:**
    Copie o arquivo de exemplo `.env.example` para um novo arquivo chamado `.env` dentro da pasta `api/`.
    ```bash
    cp api/.env.example api/.env
    ```
    Abra o arquivo `api/.env` e edite as variáveis conforme necessário:
    - `STATIC_BEARER_TOKEN`: **(Obrigatório)** Defina um token secreto forte. Você pode gerar um com o comando: `openssl rand -hex 32`.
    - `DATABASE_URL`: O caminho padrão aponta para `output/CNPJ_full.db` relativo à raiz do projeto. Ajuste se o seu banco de dados estiver em outro local.

## Executando a API

Com o ambiente virtual ativado e as dependências instaladas, inicie o servidor usando o novo script de linha de comando. A partir da raiz do projeto (`CNPJ-full/`), execute:

```bash
python api/main.py
```

O servidor usará o arquivo `api/.env` por padrão. 

### Usando um arquivo .env customizado

Você pode especificar um arquivo de configuração diferente usando a opção `--env` ou `-e`.

```bash
python api/main.py --env .env.production
```

### Ajuda

Para ver todas as opções disponíveis, use `--help`.

```bash
python api/main.py --help
```

O servidor estará disponível em `http://127.0.0.1:8000`.

- A documentação interativa (Swagger UI) estará em: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- A especificação OpenAPI estará em: [http://127.0.0.1:8000/api/v1/openapi.json](http://127.0.0.1:8000/api/v1/openapi.json)

## Endpoints da API

### Admin

- **`GET /api/v1/status`**
  - **Descrição:** Verifica a saúde e a disponibilidade da API.
  - **Autenticação:** Nenhuma.

### Consulta Direta

- **`POST /api/v1/query?page=<page_number>&page_size=<size>`**
  - **Descrição:** Executa uma consulta SQL de leitura (`SELECT`) diretamente no banco de dados e retorna os resultados de forma paginada.
  - **Autenticação:** `Bearer Token` obrigatório.
  - **Parâmetros da URL:**
    - `page` (opcional, padrão: 1): O número da página a ser retornada.
    - `page_size` (opcional, padrão: 10): O número de registros por página (máx: 200).
  - **Corpo da Requisição:**
    ```json
    {
      "sql": "SELECT * FROM estabelecimentos WHERE uf = 'SP';"
    }
    ```
  - **Formato da Resposta:**
    ```json
    {
      "total_count": 12345,
      "total_pages": 1235,
      "page": 1,
      "page_size": 10,
      "data": [
        { "coluna1": "valor1", "coluna2": "valor2" },
        { "coluna1": "valor3", "coluna2": "valor4" }
      ]
    }
    ```
  - **Exemplo com `curl` (buscando a página 2 com 5 itens por página):**
    ```bash
    curl -X POST "http://127.0.0.1:8000/api/v1/query?page=2&page_size=5" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer seu_token_secreto_aqui" \
    -d '{
      "sql": "SELECT cnpj, nome_fantasia, situacao_cadastral FROM estabelecimentos WHERE uf = \'RJ\';"
    }'
    ```

### Rede de Relacionamentos

- **`GET /api/v1/network/`**
  - **Descrição:** Monta e retorna um grafo de relacionamentos a partir de um CNPJ, CPF ou nome de sócio.
  - **Autenticação:** `Bearer Token` obrigatório.
  - **Parâmetros da Query:** `tipo_consulta`, `valor`, `nivel_max`.
  - **Exemplo com `curl`:**
    ```bash
    curl -X GET "http://127.0.0.1:8000/api/v1/network/?tipo_consulta=cnpj&valor=19131243000197&nivel_max=1" \
    -H "Authorization: Bearer seu_token_secreto_aqui"
    ```

## Segurança

- **Autenticação:** A maioria dos endpoints é protegida e requer um `Bearer Token` no cabeçalho `Authorization`.
- **Consultas SQL:** O endpoint `/api/v1/query` é poderoso e perigoso. Ele possui uma verificação básica para impedir comandos de escrita (UPDATE, DELETE, etc.) e abre o banco de dados em modo somente leitura, mas ainda assim deve ser usado com extremo cuidado. **Nunca exponha este endpoint publicamente sem camadas adicionais de segurança.**

## HTTPS/SSL em Produção

O servidor Uvicorn pode rodar com SSL se os caminhos para os arquivos de chave (`SSL_KEYFILE_PATH`) e certificado (`SSL_CERTFILE_PATH`) forem fornecidos no arquivo `.env`.

No entanto, para um ambiente de produção, a prática recomendada é usar um **servidor proxy reverso** (como Nginx, Caddy ou Traefik) na frente da sua API. O proxy reverso cuidará da terminação SSL/TLS (gerenciando os certificados) e encaminhará as requisições para a sua API via HTTP, o que é mais seguro e performático.
