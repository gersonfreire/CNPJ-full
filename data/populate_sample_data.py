#!/usr/bin/env python3
"""
Script para popular o banco de dados vazio com dados de amostra do banco completo
- Copia 10 registros aleatórios de empresas
- Copia todos os registros relacionados dessas empresas das outras tabelas
- Copia especificamente o CNPJ 33530734000131
- Garante que todas as tabelas tenham pelo menos 10 registros
"""

import sqlite3
import random
from pathlib import Path

def populate_sample_database():
    """Popula o banco vazio com dados de amostra"""
    
    # Definir caminhos
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    source_db = project_root / "output" / "CNPJ_full.db"
    target_db = current_dir / "rfb_empty.db"
    
    print("POPULANDO BANCO DE DADOS COM DADOS DE AMOSTRA")
    print("=" * 60)
    print(f"Banco origem: {source_db}")
    print(f"Banco destino: {target_db}")
    
    if not source_db.exists():
        print(f"[ERRO] Banco origem nao encontrado: {source_db}")
        return False
        
    if not target_db.exists():
        print(f"[ERRO] Banco destino nao encontrado: {target_db}")
        return False
    
    try:
        # Conectar aos bancos
        conn_source = sqlite3.connect(str(source_db))
        conn_target = sqlite3.connect(str(target_db))
        
        cursor_source = conn_source.cursor()
        cursor_target = conn_target.cursor()
        
        print("\n1. COPIANDO 10 EMPRESAS ALEATORIAS")
        print("-" * 40)
        
        # Selecionar 10 empresas aleatórias
        cursor_source.execute("""
            SELECT cnpj_basico, razao_social, natureza_juridica, 
                   qualificacao_responsavel, capital_social, 
                   porte_empresa, ente_federativo_responsavel
            FROM empresas 
            ORDER BY RANDOM() 
            LIMIT 10
        """)
        
        empresas_aleatorias = cursor_source.fetchall()
        cnpjs_basicos = [emp[0] for emp in empresas_aleatorias]
        
        print(f"Empresas selecionadas: {len(empresas_aleatorias)}")
        for i, emp in enumerate(empresas_aleatorias, 1):
            print(f"  {i}. {emp[0]} - {emp[1][:50]}...")
        
        # Inserir empresas aleatórias no banco destino
        cursor_target.executemany("""
            INSERT INTO empresas (cnpj_basico, razao_social, natureza_juridica,
                                qualificacao_responsavel, capital_social,
                                porte_empresa, ente_federativo_responsavel)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, empresas_aleatorias)
        
        print("\n2. COPIANDO EMPRESA ESPECIFICA (33530734)")
        print("-" * 40)
        
        # Buscar e copiar empresa específica
        cursor_source.execute("""
            SELECT cnpj_basico, razao_social, natureza_juridica,
                   qualificacao_responsavel, capital_social,
                   porte_empresa, ente_federativo_responsavel
            FROM empresas 
            WHERE cnpj_basico = '33530734'
        """)
        
        empresa_especifica = cursor_source.fetchone()
        if empresa_especifica:
            cursor_target.execute("""
                INSERT OR IGNORE INTO empresas (cnpj_basico, razao_social, natureza_juridica,
                                              qualificacao_responsavel, capital_social,
                                              porte_empresa, ente_federativo_responsavel)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, empresa_especifica)
            
            print(f"Empresa específica: {empresa_especifica[0]} - {empresa_especifica[1]}")
            cnpjs_basicos.append('33530734')
        else:
            print("Empresa 33530734 nao encontrada no banco origem")
        
        # Remover duplicatas da lista
        cnpjs_basicos = list(set(cnpjs_basicos))
        cnpjs_str = "', '".join(cnpjs_basicos)
        
        print(f"\nTotal de CNPJs básicos para relacionamentos: {len(cnpjs_basicos)}")
        
        print("\n3. COPIANDO ESTABELECIMENTOS RELACIONADOS")
        print("-" * 40)
        
        # Copiar estabelecimentos relacionados
        cursor_source.execute(f"""
            SELECT cnpj_basico, cnpj_ordem, cnpj_dv, identificador_matriz_filial,
                   nome_fantasia, situacao_cadastral, data_situacao_cadastral,
                   motivo_situacao_cadastral, nome_cidade_exterior, pais,
                   data_inicio_atividade, cnae_fiscal_principal, cnae_fiscal_secundaria,
                   tipo_logradouro, logradouro, numero, complemento, bairro, cep,
                   uf, municipio, ddd_1, telefone_1, ddd_2, telefone_2,
                   ddd_fax, fax, email, situacao_especial, data_situacao_especial
            FROM estabelecimentos 
            WHERE cnpj_basico IN ('{cnpjs_str}')
        """)
        
        estabelecimentos = cursor_source.fetchall()
        print(f"Estabelecimentos encontrados: {len(estabelecimentos)}")
        
        if estabelecimentos:
            cursor_target.executemany("""
                INSERT INTO estabelecimentos (
                    cnpj_basico, cnpj_ordem, cnpj_dv, identificador_matriz_filial,
                    nome_fantasia, situacao_cadastral, data_situacao_cadastral,
                    motivo_situacao_cadastral, nome_cidade_exterior, pais,
                    data_inicio_atividade, cnae_fiscal_principal, cnae_fiscal_secundaria,
                    tipo_logradouro, logradouro, numero, complemento, bairro, cep,
                    uf, municipio, ddd_1, telefone_1, ddd_2, telefone_2,
                    ddd_fax, fax, email, situacao_especial, data_situacao_especial
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, estabelecimentos)
            
            # Criar lista de CNPJs completos para CNAEs secundários
            cnpjs_completos = []
            for est in estabelecimentos:
                cnpj_completo = f"{est[0]}{est[1]}{est[2]}"  # cnpj_basico + cnpj_ordem + cnpj_dv
                cnpjs_completos.append(cnpj_completo)
        
        print("\n4. COPIANDO SOCIOS RELACIONADOS")
        print("-" * 40)
        
        # Copiar sócios relacionados
        cursor_source.execute(f"""
            SELECT cnpj_basico, identificador_socio, nome_socio_razao_social,
                   cnpj_cpf_socio, qualificacao_socio, data_entrada_sociedade,
                   pais, representante_legal, nome_representante,
                   qualificacao_representante_legal, faixa_etaria
            FROM socios 
            WHERE cnpj_basico IN ('{cnpjs_str}')
        """)
        
        socios = cursor_source.fetchall()
        print(f"Sócios encontrados: {len(socios)}")
        
        if socios:
            cursor_target.executemany("""
                INSERT INTO socios (cnpj_basico, identificador_socio, nome_socio_razao_social,
                                  cnpj_cpf_socio, qualificacao_socio, data_entrada_sociedade,
                                  pais, representante_legal, nome_representante,
                                  qualificacao_representante_legal, faixa_etaria)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, socios)
        
        print("\n5. COPIANDO DADOS DO SIMPLES RELACIONADOS")
        print("-" * 40)
        
        # Copiar dados do Simples relacionados
        cursor_source.execute(f"""
            SELECT cnpj_basico, opcao_pelo_simples, data_opcao_simples,
                   data_exclusao_simples, opcao_pelo_mei, data_opcao_mei,
                   data_exclusao_mei
            FROM simples 
            WHERE cnpj_basico IN ('{cnpjs_str}')
        """)
        
        simples_dados = cursor_source.fetchall()
        print(f"Registros Simples encontrados: {len(simples_dados)}")
        
        if simples_dados:
            cursor_target.executemany("""
                INSERT INTO simples (cnpj_basico, opcao_pelo_simples, data_opcao_simples,
                                   data_exclusao_simples, opcao_pelo_mei, data_opcao_mei,
                                   data_exclusao_mei)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, simples_dados)
        
        print("\n6. COPIANDO CNAEs SECUNDARIOS RELACIONADOS")
        print("-" * 40)
        
        # Copiar CNAEs secundários para os estabelecimentos
        if cnpjs_completos:
            cnpjs_completos_str = "', '".join(cnpjs_completos)
            cursor_source.execute(f"""
                SELECT cnpj, cnae
                FROM cnaes_secundarios 
                WHERE cnpj IN ('{cnpjs_completos_str}')
            """)
            
            cnaes_secundarios = cursor_source.fetchall()
            print(f"CNAEs secundários encontrados: {len(cnaes_secundarios)}")
            
            if cnaes_secundarios:
                cursor_target.executemany("""
                    INSERT INTO cnaes_secundarios (cnpj, cnae)
                    VALUES (?, ?)
                """, cnaes_secundarios)
        
        print("\n7. VERIFICANDO E PREENCHENDO TABELAS VAZIAS")
        print("-" * 40)
        
        # Verificar se alguma tabela ficou vazia e preencher com registros aleatórios
        tabelas = ['empresas', 'estabelecimentos', 'socios', 'simples', 'cnaes_secundarios']
        
        for tabela in tabelas:
            cursor_target.execute(f"SELECT COUNT(*) FROM {tabela}")
            count = cursor_target.fetchone()[0]
            
            if count == 0:
                print(f"[AVISO] Tabela {tabela} vazia, preenchendo com dados aleatórios...")
                
                if tabela == 'empresas':
                    cursor_source.execute("SELECT * FROM empresas ORDER BY RANDOM() LIMIT 10")
                elif tabela == 'estabelecimentos':
                    cursor_source.execute("SELECT * FROM estabelecimentos ORDER BY RANDOM() LIMIT 10")
                elif tabela == 'socios':
                    cursor_source.execute("SELECT * FROM socios ORDER BY RANDOM() LIMIT 10")
                elif tabela == 'simples':
                    cursor_source.execute("SELECT * FROM simples ORDER BY RANDOM() LIMIT 10")
                elif tabela == 'cnaes_secundarios':
                    cursor_source.execute("SELECT * FROM cnaes_secundarios ORDER BY RANDOM() LIMIT 20")
                
                dados_aleatorios = cursor_source.fetchall()
                if dados_aleatorios:
                    placeholders = ', '.join(['?' for _ in dados_aleatorios[0]])
                    cursor_target.executemany(f"INSERT INTO {tabela} VALUES ({placeholders})", dados_aleatorios)
                    print(f"  -> Inseridos {len(dados_aleatorios)} registros em {tabela}")
            else:
                print(f"Tabela {tabela}: {count} registros")
        
        # Commit das transações
        conn_target.commit()
        
        print("\n8. RESUMO FINAL")
        print("-" * 40)
        
        # Verificação final
        for tabela in tabelas:
            cursor_target.execute(f"SELECT COUNT(*) FROM {tabela}")
            count = cursor_target.fetchone()[0]
            print(f"Tabela {tabela}: {count} registros")
        
        print(f"\nBanco de dados populado com sucesso!")
        print(f"Localização: {target_db}")
        
    except Exception as e:
        print(f"[ERRO] Erro durante a população do banco: {e}")
        return False
        
    finally:
        if 'conn_source' in locals():
            conn_source.close()
        if 'conn_target' in locals():
            conn_target.close()
    
    return True

if __name__ == "__main__":
    print("Populando banco de dados com dados de amostra do CNPJ-full")
    print("=" * 60)
    
    success = populate_sample_database()
    
    if success:
        print("\nProcesso concluído com sucesso!")
    else:
        print("\nProcesso finalizado com erros!")
        exit(1)