import sys
import subprocess
import os

def run_script(command):
    """Executes a script, showing its output in real-time, and returns its exit code."""
    print(f"--- Executando comando: {' '.join(command)} ---")
    process = subprocess.run(command)
    print(f"--- Comando finalizado com código de saída: {process.returncode} ---\n")
    return process.returncode

def main():
    """
    Orquestra o processo completo de download e carga dos dados do CNPJ.
    """
    # Caminhos para os scripts
    downloader_script = os.path.join('tools', 'download_empresas_novo.py')
    cnpj_script = 'cnpj.py'

    # --- Etapa 1: Download ---
    download_command = [sys.executable, downloader_script]
    
    print("=================================================")
    print("    INICIANDO PROCESSO DE CARGA COMPLETA CNPJ    ")
    print("=================================================\n")
    
    print("--> Etapa 1 de 2: Download dos arquivos da Receita Federal...")
    
    exit_code = run_script(download_command)

    if exit_code != 0:
        print("ERRO: O download dos arquivos falhou. Abortando o processo.")
        sys.exit(exit_code)

    print("--> Download concluído com sucesso.\n")
    
    # --- Etapa 2: Processamento e Carga ---
    print("--> Etapa 2 de 2: Processamento dos arquivos e carga no banco de dados...")
    
    # Repassa os argumentos deste script para o cnpj.py
    # sys.argv[0] é o nome do script, o resto são os argumentos.
    cnpj_args = sys.argv[1:]
    cnpj_command = [sys.executable, cnpj_script] + cnpj_args
    
    exit_code = run_script(cnpj_command)

    if exit_code != 0:
        print("ERRO: O processamento dos arquivos (cnpj.py) falhou.")
        sys.exit(exit_code)
        
    print("======================================================")
    print("  PROCESSO DE CARGA COMPLETA FINALIZADO COM SUCESSO!  ")
    print("======================================================")

if __name__ == "__main__":
    main()
