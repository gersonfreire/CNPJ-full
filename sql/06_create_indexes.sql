-- Índices para otimização de consultas

-- Índice na tabela empresas
CREATE INDEX ix_empresas_cnpj_basico ON empresas (cnpj_basico);

-- Índices na tabela estabelecimentos
CREATE INDEX ix_estabelecimentos_cnpj ON estabelecimentos (cnpj_basico, cnpj_ordem, cnpj_dv);

-- Índices na tabela socios
CREATE INDEX ix_socios_cnpj_basico ON socios (cnpj_basico);
CREATE INDEX ix_socios_cpf_cnpj ON socios (cnpj_cpf_socio);

-- Índice na tabela cnaes_secundarios
CREATE INDEX ix_cnaes_cnpj ON cnaes_secundarios (cnpj);