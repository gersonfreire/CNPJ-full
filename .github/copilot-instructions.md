# AI agent quickstart for this repo (CNPJ-full)

Purpose: scripts and an optional FastAPI service to download, build and query the Brazilian Receita Federal CNPJ dataset, store it in SQLite, and explore company–partner relationship graphs with NetworkX. Start here to be productive fast.

## Big picture
- Two entry points coexist:
  - CLI batch: `cnpj.py` builds the SQLite DB from the RFB CSV/ZIPs; `consulta.py` queries it and exports CSV/GraphML/GEXF/HTML.
  - API (optional): `api/` exposes HTTP endpoints (FastAPI) to build relationship graphs over the same SQLite DB.
- Core graph logic lives in:
  - `rede_cnpj.py` (CLI) and `api/app/services/network_service.py` (API). Both traverse socios/estabelecimentos tables to build a `networkx.DiGraph` and expose helpers to serialize to pandas and graph formats.
- Data model assumptions:
  - SQLite DB named `CNPJ_full.db` (default path in `config.py` for CLI; `api/app/core/config.py` for API).
  - Tables used heavily: `socios`, `estabelecimentos`, `empresas`.
  - Node IDs: PJ = full 14-digit CNPJ; PF = masked CPF concatenated with full name (CPF mask like `***XXXX**`).
  - Edges carry attributes from `socios` rows and use `tipo='socio'`.

## Key workflows
- End-to-end automated load (recommended):
  - `executar_carga_completa.py` → calls `tools/download_empresas_novo.py` (downloads all ZIPs to `tools/downloads_cnpj`) → calls `cnpj.py` (parses CSVs, populates SQLite, optionally builds indexes).
- Manual:
  - Download: `python tools/download_empresas_novo.py` → ZIPs in `tools/downloads_cnpj`.
  - Build DB: `python cnpj.py [<input_dir> sqlite <output_dir>] [--noindex]` → `output/CNPJ_full.db`.
  - Query (CLI): `python consulta.py --tipo-consulta <cnpj|cpf|nome_socio|cpf_nome|file> --item <VALOR ou ARQ>` plus flags `--csv|--graphml|--gexf|--viz`. Defaults to `--csv` if none provided.
- API run:
  - Config via `api/.env` (see `api/app/core/config.py`). Minimal: `DATABASE_URL` and `STATIC_BEARER_TOKEN`.
  - Start: `python api/main.py` (uses Uvicorn). Docs at `/docs`, base path `/api/v1`.
  - Auth: Bearer token (`Authorization: Bearer <token>`), static value from settings.
  - Endpoint: `GET /api/v1/network?tipo_consulta=cnpj|cpf|nome_socio&valor=...&nivel_max=0..3` → returns nodes/edges JSON (see `api/app/models/response.py`).

## Conventions and patterns
- Graph building
  - Depth-limited recursion (`nivel_max`) to avoid explosion; default in CLI comes from `config.NIVEL_MAX_DEFAULT`.
  - For PF queries, CPF is masked: `***` + digits[3:9] + `**`. Matches RFB published format.
  - PJ node enrichment pulls `estabelecimentos` row; PF nodes include `cpf` and `nome`.
  - When deriving company target for edges from socios rows, resolve full CNPJ of the matriz via `estabelecimentos` where `identificador_matriz_filial = 1`.
  - Avoid back-edges using the `origem` parameter; see `_explorar_vinculos`.
- CSV outputs (CLI):
  - Uses `config.COLUNAS_CSV` and `config.SEP_CSV`.
  - Pandas ≥2.0: avoid `DataFrame.append`; use `pd.concat([df1, df2], sort=False)`.
- Paths:
  - CLI `config.py` defaults: `PATH_BD`, `SEP_CSV`, `COLUNAS_CSV`, `QUALIFICACOES`, `NIVEL_MAX_DEFAULT`.
  - API `settings` (Pydantic BaseSettings) reads `api/.env`.
- Security (API): simple static bearer token via `app/security/auth.py`.

## Gotchas the agent should handle
- Performance requires DB indexes on `empresas.cnpj` and `socios.(nome_socio_razao_social, cnpj_cpf_socio)`. The loader can create them; otherwise queries get slow at higher depths.
- Pandas 2.x breaking change: replace `.append` with `pd.concat`. Already fixed in `consulta.py`.
- Use full CNPJ for PJ nodes; for PF, concatenate masked CPF with name to make a unique stable key.
- When adding edges inside `_buscar_participacoes_societarias`, use a defined `source_node` (see recent fix replacing undefined `id_node`).
- Windows paths are common in examples; prefer raw strings or double backslashes.

## Where to look for examples
- CLI graph logic: `rede_cnpj.py` → methods `_explorar_vinculos`, `_processar_pj`, `_processar_pf`, `_buscar_participacoes_societarias`, `_adicionar_vinculo_socio`.
- API graph logic: `api/app/services/network_service.py` mirrors the above for SQLAlchemy sessions.
- Output formats: `consulta.py` supports CSV (`pessoas.csv`, `vinculos.csv`), GraphML (`rede.graphml`), GEXF (`rede.gexf`), and an HTML viewer built from `viz/template.html`.
- Config knobs: `config.py` (CLI) and `api/app/core/config.py` (API settings/schema).

## Common tasks and commands
- Build DB (default dirs): `python cnpj.py`
- Run automated workflow: `python executar_carga_completa.py --noindex`
- Query a CNPJ to CSV: `python consulta.py --tipo-consulta cnpj --item 00000000000191 --csv --output-path output`
- Start API (dev): `python api/main.py` then call `/api/v1/network?...` with Bearer token.

## Adding features safely
- Mirror changes between `rede_cnpj.py` and `api/app/services/network_service.py` to keep parity of traversal semantics and node/edge attributes.
- Keep `Graph` response schema (`api/app/models/response.py`) backward compatible if clients exist.
- If introducing new qualifiers filters, thread them from CLI args or API params down to traversal methods.

