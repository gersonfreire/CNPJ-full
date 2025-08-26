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

# Pasta onde os arquivos serão salvos
pasta_destino = "downloads_cnpj"
os.makedirs(pasta_destino, exist_ok=True)

# Função para baixar um arquivo
def baixar_arquivo(nome_arquivo):
    url = base_url + nome_arquivo
    caminho = os.path.join(pasta_destino, nome_arquivo)
    print(f"Baixando: {nome_arquivo}")
    resposta = requests.get(url, stream=True)
    if resposta.status_code == 200:
        with open(caminho, "wb") as f:
            for chunk in resposta.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✔️ Download concluído: {nome_arquivo}")
    else:
        print(f"❌ Falha ao baixar: {nome_arquivo} (Status {resposta.status_code})")

# Loop para baixar todos os arquivos
for arquivo in arquivos:
    baixar_arquivo(arquivo)
