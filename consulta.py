import os
import sys
import json
import subprocess
import argparse

import pandas as pd
import sqlite3
import networkx as nx

import config
from rede_cnpj import RedeCNPJ

def consulta(tipo_consulta, objeto_consulta, qualificacoes, path_BD, nivel_max, path_output, 
             csv=False, colunas_csv=None, csv_sep=',', graphml=False, gexf=False, viz=False, 
             path_conexoes=None):

    try:
        conBD = sqlite3.connect(path_BD)

        try:
            rede = RedeCNPJ(conBD, nivel_max=nivel_max, qualificacoes=qualificacoes)

            if tipo_consulta == 'file':
                df_file = pd.read_csv(objeto_consulta, sep=csv_sep, header=None, dtype=str)

                qtd_colunas = len(df_file.columns)

                for _, linha in df_file.iterrows():
                    if qtd_colunas >= 2:
                        try:
                            consulta_item(rede, linha[0].strip(), linha[1].strip())
                        except KeyError as e:
                            print('Item nao encontrado ({}): {}'.format(linha[0].strip(),
                                                                        linha[1].strip()))
                    else:
                        try:
                            consulta_item(rede, 'cnpj', linha[0].strip())
                        except KeyError as e:
                            print('CNPJ nao encontrado: {}'.format(linha[0].strip()))
            else:
                consulta_item(rede, tipo_consulta, objeto_consulta)

            if not os.path.exists(path_output):
                os.mkdir(path_output)

            if csv:
                # pandas.DataFrame.append was removed in pandas 2.0; use pd.concat instead
                df_nodes = pd.concat([pd.DataFrame(columns=colunas_csv), rede.dataframe_pessoas()], sort=False)

                if len(df_nodes) > 0:
                    df_nodes[colunas_csv].to_csv(os.path.join(path_output, 'pessoas.csv'), index_label='id', sep=csv_sep)

                    df_edges = rede.dataframe_vinculos()
                    if len(df_edges) > 0:
                        df_edges.to_csv(os.path.join(path_output, 'vinculos.csv'), sep=csv_sep)
                else:
                    print('Nenhum registro foi localizado. Arquivos de output nao foram gerados.')

            if graphml:
                rede.gera_graphml(os.path.join(path_output, 'rede.graphml'))

            if gexf:
                rede.gera_gexf(os.path.join(path_output, 'rede.gexf'))

            if viz:
                try:
                    with open('viz/template.html', 'r', encoding='utf-8') as template:
                        str_html = template.read().replace('<!--GRAFO-->', json.dumps(rede.json()))
                        
                    path_html = os.path.join(path_output, 'grafo.html')
                    with open(path_html, 'w', encoding='utf-8') as html:
                        html.write(str_html)

                    if config.PATH_NAVEGADOR:
                        subprocess.Popen([config.PATH_NAVEGADOR, os.path.abspath(path_html)])

                except Exception as e:
                    print('Não foi possível gerar a visualização. [{}]'.format(e))

            if path_conexoes:
                df_conexoes = pd.read_csv(path_conexoes, sep=csv_sep, header=None, dtype=str)

                qtd_colunas = len(df_conexoes.columns)

                if qtd_colunas >= 2:
                    G_undirected = rede.G.to_undirected()
                    lista_conexoes = []

                    for _, linha in df_conexoes.iterrows():
                        pessoa_A = linha[0].strip()
                        pessoa_B = linha[1].strip()

                        conexao = ''
                        try:
                            lst_pessoas_conexao = nx.shortest_path(G_undirected, pessoa_A, pessoa_B)
                            conexao = ' | '.join(lst_pessoas_conexao)
                        except:
                            conexao = 'SEM CONEXAO'

                        lista_conexoes.append((pessoa_A, pessoa_B, conexao))

                    pd.DataFrame(lista_conexoes).to_csv(os.path.join(path_output, 'conexoes.csv'),
                                                        sep=csv_sep,
                                                        header=None,
                                                        index=None)

                else:
                    print('''
Arquivo de vinculos precisa ter pelo menos duas colunas, contendo a identificacao das pessoas (CNPJ ou cpf+nome).
No caso de pessoa fisica, informar cpf seguido imediatamente do nome (ex: "***123456**NOME COMPLETO DA PESSOA").
                    ''')

            print('Consulta finalizada. Verifique o(s) arquivo(s) de saida na pasta "{}".'.format(path_output))

        except Exception as e:
            '''(.venv) PS H:\dev\rfb\CNPJ-full> & H:/dev/rfb/CNPJ-full/.venv/Scripts/python.exe h:/dev/rfb/CNPJ-full/conAttributeError("'DataFrame' object has no attribute 'append'")'''            
            print('Um erro ocorreu:\n{}'.format(e))
        finally:
            conBD.close()

    except:
        print('Nao foi possivel encontrar ou conectar ao BD {}'.format(path_BD))

def consulta_item(rede, tipo_item, item):
    if tipo_item == 'cnpj':
        rede.insere_pessoa(1, item.replace('.','').replace('/','').replace('-','').zfill(14))

    elif tipo_item == 'nome_socio':
        rede.insere_com_cpf_ou_nome(nome=item.upper())

    elif tipo_item == 'cpf':
        cpf = mascara_cpf(item.replace('.','').replace('-',''))
        rede.insere_com_cpf_ou_nome(cpf=cpf)

    elif tipo_item == 'cpf_nome':
        cpf = mascara_cpf(item[:11])
        nome = item[11:]

        rede.insere_pessoa(2,(cpf,nome))

        if len(rede.dataframe_vinculos()) == 0:
            print('Nenhum socio encontrado com cpf "{}" e nome "{}"'.format(cpf, nome))
            rede.G.remove_node(cpf+nome)
    else:
        print('Tipo de consulta invalido: {}.\nTipos possiveis: cnpj, nome_socio, cpf, cpf_nome'.format(tipo_item))

def mascara_cpf(cpf_original):
    cpf = cpf_original.zfill(11)
    if cpf[0:3] != '***':
        cpf = '***' + cpf[3:9] + '**'

    return cpf

def main():
    parser = argparse.ArgumentParser(
        description='Consulta a base de dados de CNPJ da Receita Federal e gera redes de relacionamentos.',
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        '--tipo-consulta',
        dest='tipo_consulta',
        default='cnpj',
        choices=['cnpj', 'nome_socio', 'cpf', 'cpf_nome', 'file'],
        help='''Especifica o tipo de item a ser procurado:
- cnpj: Busca empresa pelo numero do CNPJ.
- nome_socio: Busca socios pelo nome completo.
- cpf: Busca socios pelo numero do CPF (pode trazer varios socios).
- cpf_nome: Busca socios pelo CPF seguido do nome (sem espaco).
- file: Busca itens a partir de um arquivo de entrada.
(Padrão: cnpj)'''
    )
    parser.add_argument(
        '--item',
        default='33530734',
        help='Item a ser procurado (CNPJ, nome, CPF, etc.) ou caminho para o arquivo de entrada. (Padrão: 33530734000131)'
    )
    parser.add_argument(
        '--output-path',
        dest='output_path',
        default='output',
        help='Pasta onde serao salvos os arquivos gerados. (Padrão: output)'
    )

    parser.add_argument(
        '--base',
        default='H:\\dev\\rfb\\CNPJ-full\\output\\CNPJ_full.db',
        help='Caminho para o arquivo de banco de dados SQLite. Padrão: H:\\dev\\rfb\\CNPJ-full\\output\\CNPJ_full.db'
    )
    parser.add_argument(
        '--nivel',
        type=int,
        default=config.NIVEL_MAX_DEFAULT,
        help=f'Profundidade da consulta em "pulos" na rede. Padrao: {config.NIVEL_MAX_DEFAULT} (definido em config.py)'
    )
    parser.add_argument(
        '--conexoes',
        help='Caminho para o arquivo com pares de IDs para buscar conexoes entre eles.'
    )

    parser.add_argument('--csv', action='store_true', help='Gerar resultado em arquivos CSV (pessoas.csv, vinculos.csv).')
    parser.add_argument('--graphml', action='store_true', help='Gerar resultado em formato GraphML.')
    parser.add_argument('--gexf', action='store_true', help='Gerar resultado em formato GEXF (para Gephi).')
    parser.add_argument('--viz', action='store_true', help='Gerar uma visualizacao HTML interativa (grafo.html).')

    args = parser.parse_args()

    generate_csv = args.csv
    if not any([args.csv, args.graphml, args.gexf, args.viz]):
        print("Nenhum formato de saida especificado. Usando --csv como padrao.")
        generate_csv = True

    consulta(
        tipo_consulta=args.tipo_consulta,
        objeto_consulta=args.item,
        qualificacoes=config.QUALIFICACOES,
        path_BD=args.base,
        nivel_max=args.nivel,
        path_output=args.output_path,
        csv=generate_csv,
        colunas_csv=config.COLUNAS_CSV,
        csv_sep=config.SEP_CSV,
        graphml=args.graphml,
        gexf=args.gexf,
        viz=args.viz,
        path_conexoes=args.conexoes
    )

if __name__ == '__main__':
    main()
