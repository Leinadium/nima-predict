import json
import socketserver
from threading import Lock
from time import perf_counter
from termcolor import colored
from keras.models import Sequential
from sklearn.feature_extraction.text import CountVectorizer

from rede_neural import classificar

modelo = None
vectorizer = None
porta = None
lock = Lock()


def print_blue(*args): print(colored(' '.join([str(a) for a in args]), 'blue'))


def print_red(*args): print(colored(' '.join([str(a) for a in args]), 'red'))


def print_green(*args): print(colored(' '.join([str(a) for a in args]), 'green'))


class TCPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        if not (isinstance(modelo, Sequential) and isinstance(vectorizer, CountVectorizer)):
            print_red("Abortando, pois modelo ou vectorizer não foram definidos")
            return

        data = self.request.recv(4096).decode('utf-8')
        print_blue(f"\n\nRecebi algum dado: ", data[:20])
        tempo_inicial = perf_counter()

        try:
            data_dict = json.loads(data)
            print_blue("\tJSON decodificado com sucesso:")
            print_green(f"\t\t{str(data_dict)[:40]}...")
        except json.JSONDecodeError:
            print_red("  Erro decodificando JSON")
            data_dict = None

        # processando
        res: dict = {}
        if data_dict is not None:
            print_blue("Executando rede neural")
            with lock:
                res = classificar(
                    model=modelo,
                    vec=vectorizer,
                    dados=data_dict
                )

        # enviando resposta de volta
        res_em_string = json.dumps(res)
        print_blue("Enviando resposta: ")
        print_green(f"\t{res_em_string[:40]}...")

        self.request.sendall(res_em_string.encode('utf-8'))
        tempo_decorrido_ms = (perf_counter() - tempo_inicial) * 1000
        print(colored("Tempo de execução: ", 'blue'), colored(f"{tempo_decorrido_ms} ms", 'yellow'))


def configurar(m: Sequential, v: CountVectorizer, porta_server):
    global modelo, vectorizer, porta
    modelo = m
    vectorizer = v
    porta = porta_server


def server_loop():
    if not isinstance(porta, int):
        print_red("Abortando, porta do servidor não foi definida")
        return

    CONNECTION = "", porta
    with socketserver.TCPServer(CONNECTION, TCPHandler) as server:
        print_blue(f"Servidor ouvindo em {server.server_address}")
        try:
            server.serve_forever()  # can only be stopped by CTRL+C
        except KeyboardInterrupt:
            print_blue("Fechando servidor")
            return
