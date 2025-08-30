-- Script completo para criação do schema do banco CNPJ_full.db
-- Execute este arquivo para criar todas as estruturas do banco de dados

-- ==================================================
-- CRIAÇÃO DAS TABELAS
-- ==================================================

-- Tabela de Empresas
CREATE TABLE "empresas" (
    "cnpj_basico" TEXT,
    "razao_social" TEXT,
    "natureza_juridica" TEXT,
    "qualificacao_responsavel" TEXT,
    "capital_social" REAL,
    "porte_empresa" TEXT,
    "ente_federativo_responsavel" TEXT
);

-- Tabela de Estabelecimentos
CREATE TABLE "estabelecimentos" (
    "cnpj_basico" TEXT,
    "cnpj_ordem" TEXT,
    "cnpj_dv" TEXT,
    "identificador_matriz_filial" TEXT,
    "nome_fantasia" TEXT,
    "situacao_cadastral" TEXT,
    "data_situacao_cadastral" TEXT,
    "motivo_situacao_cadastral" TEXT,
    "nome_cidade_exterior" TEXT,
    "pais" TEXT,
    "data_inicio_atividade" TEXT,
    "cnae_fiscal_principal" TEXT,
    "cnae_fiscal_secundaria" TEXT,
    "tipo_logradouro" TEXT,
    "logradouro" TEXT,
    "numero" TEXT,
    "complemento" TEXT,
    "bairro" TEXT,
    "cep" TEXT,
    "uf" TEXT,
    "municipio" TEXT,
    "ddd_1" TEXT,
    "telefone_1" TEXT,
    "ddd_2" TEXT,
    "telefone_2" TEXT,
    "ddd_fax" TEXT,
    "fax" TEXT,
    "email" TEXT,
    "situacao_especial" TEXT,
    "data_situacao_especial" TEXT
);

-- Tabela de Sócios
CREATE TABLE "socios" (
    "cnpj_basico" TEXT,
    "identificador_socio" TEXT,
    "nome_socio_razao_social" TEXT,
    "cnpj_cpf_socio" TEXT,
    "qualificacao_socio" TEXT,
    "data_entrada_sociedade" TEXT,
    "pais" TEXT,
    "representante_legal" TEXT,
    "nome_representante" TEXT,
    "qualificacao_representante_legal" TEXT,
    "faixa_etaria" TEXT
);

-- Tabela de CNAEs Secundários
CREATE TABLE "cnaes_secundarios" (
    "cnpj" TEXT,
    "cnae" TEXT
);

-- Tabela do Simples Nacional
CREATE TABLE "simples" (
    "cnpj_basico" TEXT,
    "opcao_pelo_simples" TEXT,
    "data_opcao_simples" TEXT,
    "data_exclusao_simples" TEXT,
    "opcao_pelo_mei" TEXT,
    "data_opcao_mei" TEXT,
    "data_exclusao_mei" TEXT
);

-- ==================================================
-- CRIAÇÃO DOS ÍNDICES
-- ==================================================

-- Índice na tabela empresas
CREATE INDEX ix_empresas_cnpj_basico ON empresas (cnpj_basico);

-- Índices na tabela estabelecimentos
CREATE INDEX ix_estabelecimentos_cnpj ON estabelecimentos (cnpj_basico, cnpj_ordem, cnpj_dv);

-- Índices na tabela socios
CREATE INDEX ix_socios_cnpj_basico ON socios (cnpj_basico);
CREATE INDEX ix_socios_cpf_cnpj ON socios (cnpj_cpf_socio);

-- Índice na tabela cnaes_secundarios
CREATE INDEX ix_cnaes_cnpj ON cnaes_secundarios (cnpj);