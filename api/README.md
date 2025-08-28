# API de Consulta de Rede CNPJ

Esta é uma API RESTful desenvolvida com FastAPI para consultar e explorar a rede de relacionamentos (empresas e sócios) da base de dados públicos de CNPJ da Receita Federal.

A API é projetada para ser independente e oferece uma interface moderna e documentada para as funcionalidades de consulta do projeto.

## ✨ Features

- **Framework Moderno:** Construída com [FastAPI](https://fastapi.tiangolo.com/), garantindo alta performance.
- **Documentação Automática:** Interface interativa do Swagger UI (`/docs`) e ReDoc (`/redoc`) gerada automaticamente.
- **Autenticação:** Endpoints protegidos por autenticação `Bearer Token`.
- **Configuração Flexível:** Todas as configurações são gerenciadas através de um arquivo `.env`.
- **Lógica de Negócio Isolada:** A lógica de consulta à rede é separada da camada de API, seguindo as melhores práticas.
- **Suporte a HTTPS:** Capacidade de rodar com certificados SSL.

---

## 🚀 Setup e Instalação

Siga os passos abaixo para configurar e executar a API localmente.

### 1. Pré-requisitos

- Python 3.8+
- O banco de dados SQLite (`CNPJ_full.db`) gerado pelos scripts da raiz do projeto deve existir.

### 2. Configuração do Ambiente

Primeiro, crie e configure o arquivo de ambiente:

```bash
# Navegue até a pasta da api
cd api

# Copie o arquivo de exemplo para criar seu próprio arquivo de configuração
# No Windows, use copy:
# copy .env.example .env
# No Linux/macOS, use cp:
# cp .env.example .env
```

Abra o arquivo `.env` recém-criado e edite as variáveis conforme necessário:
- `STATIC_BEARER_TOKEN`: **Obrigatório.** Defina um token secreto para a autenticação.
- `DATABASE_URL`: Verifique se o caminho para o seu banco de dados (`CNPJ_full.db`) está correto.
- `API_PORT`: Altere a porta se a padrão (`8000`) estiver em uso.

### 3. Instalação das Dependências

Certifique-se de que seu ambiente virtual (`.venv`) está ativado. Em seguida, instale os pacotes necessários:

```bash
# Estando na pasta raiz do projeto (CNPJ-full)
# O comando usa o pip do ambiente virtual para instalar os pacotes da api
.venv\Scripts\pip install -r api\requirements.txt
```

---

## ▶️ Executando a API

Com o ambiente configurado e as dependências instaladas, inicie o servidor:

```bash
# Navegue até a pasta da api
cd api

# Inicie o servidor
python main.py
```

O terminal indicará o endereço e a porta em que a API está rodando (ex: `http://0.0.0.0:8000`).

---

## 📖 Documentação e Uso

### Acessando a Interface do Swagger

Após iniciar a API, abra seu navegador e acesse:

[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Você verá a documentação interativa de todos os endpoints.

### Autenticação

Os endpoints de consulta são protegidos. Para usá-los através do Swagger UI:

1.  Clique no botão **Authorize** no canto superior direito.
2.  No campo `Value`, cole o token que você definiu para `STATIC_BEARER_TOKEN` no seu arquivo `.env`.
3.  Clique em **Authorize** e feche o pop-up.

Agora você pode testar os endpoints que requerem autenticação.

### Exemplo de Consulta

O principal endpoint é o `/api/v1/network`.

1.  Expanda a seção do endpoint `GET /api/v1/network`.
2.  Clique em **Try it out**.
3.  Preencha os parâmetros:
    - **tipo_consulta**: `cnpj`
    - **valor**: `33530734000131` (ou outro CNPJ de 14 dígitos)
    - **nivel_max**: `1`
4.  Clique em **Execute**.

A resposta será um JSON contendo os nós (empresas, sócios) e as arestas (vínculos) da rede encontrada.

---

## ⚙️ Variáveis de Configuração (`.env`)

| Variável              | Descrição                                                                                             | Padrão                                                 |
| --------------------- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| `API_HOST`            | O endereço IP em que a API irá escutar. `0.0.0.0` permite acesso pela rede.                            | `0.0.0.0`                                              |
| `API_PORT`            | A porta em que a API irá escutar.                                                                     | `8000`                                                 |
| `API_RELOAD`          | `true` para reiniciar o servidor automaticamente após alterações no código (desenvolvimento).         | `true`                                                 |
| `STATIC_BEARER_TOKEN` | O token secreto usado para autenticação.                                                              | `seu_token_secreto_aqui`                               |
| `DATABASE_URL`        | A [string de conexão SQLAlchemy](https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls) para o banco de dados. | `sqlite:///H:/.../output/CNPJ_full.db` |
| `SSL_KEYFILE_PATH`    | Caminho para o arquivo de chave SSL para rodar em HTTPS. Se vazio, usa HTTP.                          | `""`                                                   |
| `SSL_CERTFILE_PATH`   | Caminho para o arquivo de certificado SSL para rodar em HTTPS. Se vazio, usa HTTP.                    | `""`                                                   |

```