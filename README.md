# Dados Públicos CNPJ - Conversão para CSV/SQLITE e Consultas

Utilitário em Python para baixar e carregar a base completa de CNPJ [disponibilizada pela Receita Federal](http://200.152.38.155/CNPJ/) e transformá-la em um banco de dados SQLite para fácil consumo. Processa dados de empresas, estabelecimentos, sócios e Simples Nacional.

Possibilita também fazer consultas de empresas ou sócios e gravar resultados em CSV ou em grafo de relacionamentos.

![Grafo](img/grafo.png?raw=true "Grafo")

## Requisitos

### Python
Versão 3.6 ou superior.

### Instalar Bibliotecas
Antes de executar qualquer script, instale as dependências necessárias:
`$ pip install -r requirements.txt`

---

## Modo Automatizado (Recomendado)

Para baixar e processar os dados da Receita Federal de forma totalmente automática, utilize o script `executar_carga_completa.py`. Ele orquestra o download e a carga no banco de dados sem necessidade de intervenção.

`python executar_carga_completa.py [argumentos_para_o_cnpj.py]`

O script executará as duas etapas principais:
1.  **Download:** Executa `tools/download_empresas_novo.py` para baixar todos os arquivos `.zip` de dados do site da RFB para a pasta `tools/downloads_cnpj`.
2.  **Carga:** Executa `cnpj.py` para processar os arquivos baixados e criar o banco de dados SQLite.

Por padrão, `cnpj.py` usará a pasta `tools/downloads_cnpj` como entrada e salvará o banco `CNPJ_full.db` na pasta `output`.

### Personalizando a Carga Automatizada

É possível passar argumentos para a etapa de carga. Os argumentos fornecidos ao `executar_carga_completa.py` serão repassados diretamente para o `cnpj.py`.

**Exemplo:** Para não gerar índices no banco de dados ao final da carga.
`python executar_carga_completa.py --noindex`

Consulte a seção do `cnpj.py` abaixo para ver todos os argumentos disponíveis.

---

## Etapas Manuais

Se preferir, você pode executar cada etapa do processo manualmente.

### 1. Download dos Dados

O script `tools/download_empresas_novo.py` é responsável por baixar os arquivos de dados públicos do site da Receita Federal.

`python tools/download_empresas_novo.py`

Ele irá baixar todos os arquivos `.zip` para a pasta `tools/downloads_cnpj`, pulando arquivos que já existirem no local.

### 2. Carga para SQLite

O script `cnpj.py` foi atualizado para processar os arquivos `.zip` no novo formato CSV disponibilizado pela Receita Federal e carregá-los em um banco de dados SQLite.

**Uso:**
`python cnpj.py [<path_input> <output:sqlite> <path_output>] [--noindex]`

**Funcionalidades:**
- **Valores Padrão:** Se executado sem argumentos, o script assume os seguintes valores:
  - Diretório de entrada: `tools/downloads_cnpj`
  - Formato de saída: `sqlite`
  - Diretório de saída: `output`
- **Progresso Detalhado:** Durante a execução, o script exibe o total de registros lidos por arquivo e o total acumulado na tabela, fornecendo um feedback claro do progresso.

**Argumentos:**
- `<path_input>`: Diretório contendo os arquivos `.zip` da RFB.
- `<output:sqlite>`: Formato de saída. Atualmente, apenas 'sqlite' é suportado.
- `<path_output>`: Diretório onde o banco de dados SQLite será salvo.
- `[--noindex]`: Opcional. Não gera índices no banco de dados ao final.

**Exemplos:**
- **Usando valores padrão:**
  `python cnpj.py`
- **Especificando os caminhos:**
  `python cnpj.py "dados_rfb" sqlite "output"`

---
# Consultas

**Novidade!** Agora é possível fazer consultas que além de trazer empresas e sócios específicos, traz a rede de relacionamentos na profundidade desejada. Os resultados podem ser salvos em formato tabular e/ou em formatos variados de grafos de relacionamento, que podem ser visualizados de forma interativa no navegador ou abertos em softwares que suportem os formatos especificados, como o [Gephi](https://gephi.org/).

Essa funcionalidade é exclusiva para a base sqlite gerada usando o `cnpj.py`. No entanto, pode ser relativamente simples adaptar o código para funcionar com outros SGBDs ou arquivos sqlite gerados usando outra nomenclatura.

## Configurações prévias
Para executar o script de consulta, é necessário que seu sistema contenha as instalações especificadas acima e, além disso, é necessário:

#### Networkx 2.x (pacote de criação, manipulação e análise de grafos/redes)

É **IMPRESCINDÍVEL** que índices sejam criados nos campos `cnpj` das tabelas `empresas` e `socios`, e nos campos `nome_socio` e `cnpj_cpf_socio` da tabela `socios`. Do contrário, as consultas se tornam insuportavelmente lentas ou até mesmo inviáveis dependendo da profundidade. O script de carga (cnpj.py) foi atualizado para opcionalmente gerar os índices mais importantes automaticamente ao final da carga.

## Instruções Básicas:

Uso: `python consulta.py <tipo consulta> <item|arquivo input> <caminho output> [--base <arquivo sqlite>]`
`[--nivel <int>] [--csv] [--graphml] [--gexf] [--viz]`

#### Argumentos obrigatórios:

`<tipo consulta>`: Especifica o tipo de item a ser procurado. Opções:
* **cnpj:** Busca empresa pelo número do CNPJ.

* **nome_socio:** Busca sócios pelo nome completo.

* **cpf:** Busca sócios pelo número do CPF.
      (Pode trazer vários sócios, uma vez que apenas seis dígitos são fornecidos pela RF)
      
* **cpf_nome:** Busca sócios pelo número do CPF seguido (sem espaço) do nome completo.

* **file:** Arquivo que contem mais de um item a ser buscado.
        Caso o arquivo tenha apenas um dado por linha, será tratado como número de CNPJ.
        Caso o arquivo tenha mais de um dado separado por `;`, o primeiro
        indica um dos tipos acima, e o segundo o item a ser buscado.
        (outro separador pode ser definido em `SEP_CSV` no `config.py`) 

`<item|arquivo input>`: Item a ser procurado, de acordo com `<tipo consulta>`.
  
`<caminho output>`: Pasta onde serão salvos os arquivos gerados.

#### Argumentos opcionais:

`--base`: Especifica o arquivo do banco de dados de CNPJ em formato sqlite.
           Caso não seja especificado, usa o `PATH_BD` definido no `config.py`

`--nivel`: Especifica a profundidade da consulta em número de "pulos".
            Exemplo: Caso seja especificado `--nivel 1`, busca o item e as empresas ou pessoas diretamente relacionadas.
            Caso não seja especificado, usa o `NIVEL_MAX_DEFAULT` no `config.py`

`--csv`: Para gerar o resultado em arquivos csv.
          São gerados dois arquivos, `pessoas.csv` e `vinculos.csv`.

`--graphml`: Para gerar o resultado em grafo no formato GRAPHML.

`--gexf`: Para gerar o resultado em grafo no formato GEXF. 
           Pode ser aberto com o software [Gephi](https://gephi.org/)

 `--viz`: Para gerar um HTML interativo com o resultado em grafo.
          Para abrir automaticamente o navegador, informar o `PATH_NAVEGADOR` 
          no `config.py`. Do contrário, basta abrir o arquivo `grafo.html` gerado 
          em `<caminho output>` com o navegador de preferência.

#### Exemplos:

`python consulta.py cnpj 00000000000191 folder --nivel 1 --viz`

`python consulta.py file data/input.csv pasta --csv --gexf`

`python consulta.py nome_socio "FULANO SICRANO" output --graphml --viz`

#### Atenção:

Especifique o nível de profundidade da rede com moderação, uma vez que, dependendo das empresas ou pessoas buscadas, a quantidade de relacionados pode crescer exponencialmente, atingindo facilmente centenas ou milhares de registros, o que resulta na execução intensiva de queries no BD. Nível 3 é um bom parâmetro.

#### Configuração

No `config.py`, as seguintes configurações são definidas:

`PATH_BD`: Caminho para o arquivo de banco de dados da Receita Federal convertido em sqlite. 
Pode ser sobrescrito em tempo de execução usando o argumento `--base`.

`NIVEL_MAX_DEFAULT`: Nível máximo default para a profundidade das buscas.
Pode ser sobrescrito em tempo de execução usando o argumento `--nivel <num>`

`PATH_NAVEGADOR`: Caminho completo para o executável do navegador preferido se desejar que a visualização seja automaticamente apresentada ao final da execução da consulta (se argumento `--viz` for utilizado). Caso vazio, apenas gera o html na pasta de saída.

`SEP_CSV`: Especifica o separador a ser considerado tanto para os arquivos csv de saída (caso seja utilizado o argumento `--csv`), quanto para o arquivo de entrada no caso do uso de `file` como `<tipo consulta>`.

`COLUNAS_CSV`: Especifica a lista de colunas a serem incluídas no arquivo `pessoas.csv` quando usado o argumento `--csv`.

`QUALIFICACOES`: Especifica a lista de qualificações de sócios a serem consideradas na busca dos relacionamentos. Caso `TODAS`, qualquer relação de sociedade listada no BD é considerada.

## Trabalhando diretamente com a classe RedeCNPJ

O objetivo do `consulta.py` é disponibilizar uma interface por linha de comando para facilitar a extração/visualização da rede de relacionamentos de empresas e pessoas a partir da base de dados da RF convertida em sqlite. Ele é uma "casca" para a classe `RedeCNPJ` definida em `rede_cnpj.py`, onde fica a inteligência de navegação no BD e criação de rede/grafo usando o pacote `networkx`, além de métodos para conversão em DataFrames pandas e formatos diversos de representação de estruturas em grafo.

Em seu projeto você pode instanciar diretamente a `RedeCNPJ` especificando a conexão ao BD e o nível máximo de navegação nos relacionamentos, usar os métodos de inserção de empresas/pessoas para montar a rede (sem se preocupar com a navegação para as relacionadas), e usar os métodos para conversão da rede em DataFrame ou formatos diversos de representação de grafos.

E dessa forma você pode também usar o grafo gerado (atributo "G" da classe) para incrementá-lo a partir de outras fontes de dados de interesse para seu caso de uso e usar os diversos algoritmos disponibilizados pela biblioteca `networkx`, como por exemplo detecção de ciclos.

## TO DO

* Aprimorar a documentação do código (principalmente da classe RedeCNPJ) e as instruções neste README.
