
"""
    Download de arquivos do portal da transparência do governo brasileiro
    
    https://dadosabertos.rfb.gov.br/
    
    https://arquivos.receitafederal.gov.br/dados/cnpj/dados_abertos_cnpj/?C=N;O=D
    
    https://github.com/gersonfreire/CNPJ-full
    
    https://dados.gov.br/dados/conjuntos-dados
"""

# add python parent dir to sys.path
import sys, os

import requests
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util import *

# Lista de arquivos para download
files = [
    'Empresas0.zip',
    'Empresas1.zip',
    'Empresas2.zip',
    'Empresas3.zip',
    'Empresas4.zip',
    'Empresas5.zip',
    'Empresas6.zip',
    'Empresas7.zip',
    'Empresas8.zip',
    'Empresas9.zip',
    'Estabelecimentos.zip',
    'Socios.zip',
    'SocioAdministrador.zip',
    'SocioControlador.zip',
    'SocioExterior.zip',
    'SocioNatural.zip',
    'SocioPessoaJuridica.zip',
    'SocioRepresentanteLegal.zip',
    'SocioResponsavel.zip',
    'SocioSimples.zip'
]

# -----------------------------------------------------------------------------
# Constantes
# -----------------------------------------------------------------------------

# URL base para download dos arquivos
base_url = 'https://dadosabertos.rfb.gov.br/CNPJ/'

import logging

# Configuração básica do registro de eventos
log_file = 'download_govbr.log'
logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(message)s",
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]    
    )

# Registro de eventos
logging.debug('Inicio do programa')

# -----------------------------------------------------------------------------
# Funções
# -----------------------------------------------------------------------------
def download_file(url, file_name):
    """
        Download de arquivo
    """
    # Download do arquivo
    logging.debug(f'Download: {url}')
    r = requests.get(url, allow_redirects=True)
    open(file_name, 'wb').write(r.content)

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if __name__ == '__main__':

    # Cria diretório de destino
    if not os.path.exists('data'):
        os.makedirs('data')

    # Download dos arquivos
    for file in files:
        url = base_url + file
        file_name = os.path.join('data', file)
        download_file(url, file_name)

    # Registro de eventos
    logging.debug('Fim do programa')
