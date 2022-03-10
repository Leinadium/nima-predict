import argparse
from os import path
from termcolor import colored
import colorama

from server import configurar, server_loop
from rede_neural import carregar_modelo, carregar_vectorizer

colorama.init()

# argumentos
description = "Servidor responsável por receber produções e responder quais delas são relacionadas a meio ambiente"

parser = argparse.ArgumentParser(description=description)
parser.add_argument('modelo', metavar='MODELO.h', type=str, help="path/para/modelo.h")
parser.add_argument('vectorizer', metavar='VECTORIZER.pkl', type=str, help='path/para/vectorizer.pkl')
parser.add_argument('porta', metavar='PORTA', type=int, nargs='?', help='porta do servidor. Padrão: 9999', default=9999)

args = parser.parse_args()

# verificando os arquivos
path_modelo = args.modelo
path_vec = args.vectorizer

if not path.isfile(path_modelo):
    print(colored("Arquivo não encontrado: ", 'red'), path_modelo)
    exit(-1)

if not path.isfile(path_vec):
    print(colored("Arquivo não encontrado: ", 'red'), path_vec)
    exit(-1)

# configurando os modelos
try:
    configurar(
        m=carregar_modelo(path_modelo),
        v=carregar_vectorizer(path_vec),
        porta_server=args.porta
    )
except Exception as e:
    print(colored(f"Erro configurando servidor: {e}"), 'red')
    exit(-1)

# iniciando loop
server_loop()
