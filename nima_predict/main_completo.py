import colorama
from os import path
from time import time
from termcolor import colored, cprint
from franz.openrdf.sail.allegrographserver import RepositoryConnection

from classificacao import conexao
from rede_neural import carregar_modelo, carregar_vectorizer, classificar

colorama.init()


def cinput(texto, cor):
    print(colored(texto, cor), end='')
    return input()


if __name__ == "__main__":

    # carregando arquivos
    path_para_modelo = cinput("Digite o caminho para o modelo neural: ", 'blue')
    if not path.exists(path_para_modelo):
        print(colored('Arquivo não encontrado. Abortando', 'red'))
        raise FileNotFoundError

    path_para_vectorizer = cinput("Digite o caminho para o vetorizador: ", 'blue')
    if not path.exists(path_para_vectorizer):
        print(colored('Arquivo não encontrado. Abortando', 'red'))
        raise FileNotFoundError

    conexao.checa_variavel_ambiente()
    cprint('Pré configuração finalizada\n', 'blue')

    # conectando com o banco
    repo: RepositoryConnection = conexao.conectar()

    # carregando producoes
    cprint('Carregando todas as produções', 'blue')
    dicionario_completo = conexao.obter_dicionario_completo(repo)
    cprint(f"Finalizado [{len(dicionario_completo)} produções]")

    # fazendo a predição
    cprint('Executando o modelo de rede neural sobre as produções', 'blue')
    t = time()
    dicionario_final = classificar(
        model=carregar_modelo(path_para_modelo),
        vec=carregar_vectorizer(path_para_vectorizer),
        dados=dicionario_completo
    )

    cprint(f'Finalizado [{time() - t} s]', 'blue')

    # fazendo a segunda conexão
    r = cinput('Digite o nome do repositorio para armazenar os resultados: ', 'cyan')
    cprint('Conectando ao novo repositório', 'blue')
    repo2 = conexao.conectar_repositorio(
        repositorio=r
    )
    cprint(f'Conectado com sucesso ao repositório [size: {repo2.size()}]', 'blue')

    # salvando
    cprint(f'Executando as inserções', 'blue')
    conexao.guardar_dicionario(
        repo=repo2,
        dicionario=dicionario_final,
        cad_puc_namespace=conexao.obter_cad_puc_namespace(repo)
    )
    cprint('Finalizando', 'blue')

    repo.close()
    repo2.close()
