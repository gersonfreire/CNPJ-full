import requests
import os

# URL base da página
base_url = "https://arquivos.receitafederal.gov.br/dados/cnpj/dados_abertos_cnpj/2025-08/"

# Lista de arquivos encontrados na página
arquivos = [
    "Cnaes.zip", "Empresas0.zip", "Empresas1.zip", "Empresas2.zip", "Empresas3.zip",
    "Empresas4.zip", "Empresas5.zip", "Empresas6.zip", "Empresas7.zip", "Empresas8.zip",
    "Empresas9.zip", "Estabelecimentos0.zip", "Estabelecimentos1.zip", "Estabelecimentos2.zip",
    "Estabelecimentos3.zip", "Estabelecimentos4.zip", "Estabelecimentos5.zip", "Estabelecimentos6.zip",
    "Estabelecimentos7.zip", "Estabelecimentos8.zip", "Estabelecimentos9.zip", "Motivos.zip",
    "Municipios.zip", "Naturezas.zip", "Paises.zip", "Qualificacoes.zip", "Simples.zip",
    "Socios0.zip", "Socios1.zip", "Socios2.zip", "Socios3.zip", "Socios4.zip", "Socios5.zip",
    "Socios6.zip", "Socios7.zip", "Socios8.zip", "Socios9.zip"
]

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Pasta onde os arquivos serão salvos
pasta_destino = os.path.join(script_dir, "downloads_cnpj")
os.makedirs(pasta_destino, exist_ok=True)

# Initialize flags
overwrite_all = False
skip_all = False

# Loop para baixar todos os arquivos
for nome_arquivo in arquivos:
    caminho = os.path.join(pasta_destino, nome_arquivo)

    # Check if file exists and what to do
    if os.path.exists(caminho):
        if skip_all:
            print(f"Skipping '{nome_arquivo}' (skip all enabled).")
            continue

        if not overwrite_all:
            prompt = f"'{nome_arquivo}' already exists. Overwrite? (y/n/a/s) (yes/no/all/skip all): "
            answer = input(prompt).lower()

            if answer == 'a':
                overwrite_all = True
            elif answer == 's':
                skip_all = True
                print(f"Skipping '{nome_arquivo}' and all subsequent existing files.")
                continue
            elif answer != 'y': # This covers 'n' and anything else
                print(f"Skipping '{nome_arquivo}'.")
                continue

    # Download the file
    url = base_url + nome_arquivo
    print(f"Baixando: {nome_arquivo}")
    try:
        resposta = requests.get(url, stream=True)
        resposta.raise_for_status()  # Raise an exception for bad status codes
        with open(caminho, "wb") as f:
            for chunk in resposta.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✔️ Download concluído: {nome_arquivo}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Falha ao baixar: {nome_arquivo} ({e})")

print("\nAll files have been processed.")
