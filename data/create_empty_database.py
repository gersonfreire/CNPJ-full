#!/usr/bin/env python3
"""
Script para criar um banco de dados SQLite vazio com a estrutura do CNPJ-full
Executa os scripts DDL da pasta sql/ para criar todas as tabelas e índices
"""

import sqlite3
import os
import glob
from pathlib import Path

def create_empty_database():
    """Cria o banco de dados vazio e executa os scripts DDL"""
    
    # Definir caminhos
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    sql_dir = project_root / "sql"
    db_path = current_dir / "rfb_empty.db"
    
    print(f"Diretório do projeto: {project_root}")
    print(f"Diretório SQL: {sql_dir}")
    print(f"Banco de dados será criado em: {db_path}")
    
    # Remover banco existente se houver
    if db_path.exists():
        print("Removendo banco de dados existente...")
        db_path.unlink()
    
    # Conectar ao banco (cria automaticamente se não existir)
    print("Criando banco de dados vazio...")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Verificar se diretório SQL existe
        if not sql_dir.exists():
            raise FileNotFoundError(f"Diretório SQL não encontrado: {sql_dir}")
        
        # Buscar por scripts SQL ordenados
        sql_files = sorted(sql_dir.glob("*.sql"))
        
        if not sql_files:
            raise FileNotFoundError(f"Nenhum arquivo SQL encontrado em: {sql_dir}")
        
        print(f"Encontrados {len(sql_files)} arquivos SQL:")
        for sql_file in sql_files:
            print(f"  - {sql_file.name}")
        
        # Executar o script principal (00_create_database_schema.sql)
        main_script = sql_dir / "00_create_database_schema.sql"
        
        if main_script.exists():
            print(f"\nExecutando script principal: {main_script.name}")
            with open(main_script, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Dividir por comandos SQL (separados por ponto e vírgula)
            sql_commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]
            
            for i, command in enumerate(sql_commands, 1):
                if command.strip():
                    try:
                        cursor.execute(command)
                        print(f"  [OK] Comando {i} executado com sucesso")
                    except sqlite3.Error as e:
                        print(f"  [ERRO] Erro no comando {i}: {e}")
                        print(f"    Comando: {command[:100]}...")
            
            conn.commit()
            print(f"\nScript {main_script.name} executado com sucesso!")
        
        else:
            print("Script principal não encontrado, executando scripts individuais...")
            
            # Executar scripts individuais (pular o script principal se não existir)
            individual_scripts = [f for f in sql_files if f.name != "00_create_database_schema.sql"]
            
            for sql_file in individual_scripts:
                print(f"\nExecutando: {sql_file.name}")
                
                try:
                    with open(sql_file, 'r', encoding='utf-8') as f:
                        sql_content = f.read()
                    
                    # Executar comandos SQL
                    sql_commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]
                    
                    for command in sql_commands:
                        if command.strip():
                            cursor.execute(command)
                    
                    conn.commit()
                    print(f"  [OK] {sql_file.name} executado com sucesso!")
                    
                except Exception as e:
                    print(f"  [ERRO] Erro ao executar {sql_file.name}: {e}")
        
        # Verificar estrutura criada
        print("\n" + "="*50)
        print("VERIFICANDO ESTRUTURA CRIADA")
        print("="*50)
        
        # Listar tabelas criadas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"\nTabelas criadas ({len(tables)}):")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Listar índices criados
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
        indexes = cursor.fetchall()
        print(f"\nÍndices criados ({len(indexes)}):")
        for index in indexes:
            print(f"  - {index[0]}")
        
        print(f"\nBanco de dados '{db_path.name}' criado com sucesso!")
        print(f"Localização: {db_path}")
        
    except Exception as e:
        print(f"Erro durante a criação do banco: {e}")
        return False
        
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    print("Criando banco de dados SQLite vazio com estrutura CNPJ-full")
    print("-" * 60)
    
    success = create_empty_database()
    
    if success:
        print("\nProcesso concluído com sucesso!")
    else:
        print("\nProcesso finalizado com erros!")
        exit(1)