from os import environ
from termcolor import colored, cprint
from franz.openrdf.exceptions import ServerException
from franz.openrdf.sail.allegrographserver import RepositoryConnection, AllegroGraphServer

# para typing
from typing import List, Dict
from franz.openrdf.repository import Repository
from franz.openrdf.query.queryresult import ListBindingSet
from franz.miniclient.request import RequestError


def cinput(texto, cor):
    print(colored(texto, cor), end='')
    return input()


def checa_variavel_ambiente():
    for env in ["AGRAPH_HOST", "AGRAPH_PORT", "AGRAPH_USER", "AGRAPH_PASSWORD"]:
        if env not in environ:
            cprint(f'Declare a variavel de ambiente {env}, e execute novamente.', 'red')
            exit(-1)


def conectar() -> RepositoryConnection:
    """
    Tenta conectar no servidor AllegroGraph.

    Essa função precisa que as seguintes variaveis de ambiente existam:

        * AGRAPH_HOST
        * AGRAPH_PORT
        * AGRAPH_USER
        * AGRAPH_PASSWORD

    Ela irá perguntar os repositórios para criar uma federação diretamente ao usuário, por meio
    de `input`.
    """

    checa_variavel_ambiente()

    server = AllegroGraphServer()
    catalogo = server.openCatalog(None)                  # catalogo root
    lista_conexoes: List[RepositoryConnection] = list()  # repositorios

    while (r := cinput("Digite o nome do repositório, ou [ENTER] para finalizar: ", 'blue')) != '':
        try:
            repo = catalogo.getRepository(  # acessando somente o repositorio
                name=r.strip(),
                access_verb=Repository.OPEN
            ).getConnection()  # ja conectando

            # pegando o tamanho dele para imprimir
            size = repo.size()
            cprint(f'Repositório contendo {size} tuplas', 'green')

            lista_conexoes.append(repo)

        except ServerException:  # quando nao encontra o repositorio
            cprint(f'Repositorio {r} nao encontrado. Tente novamente', 'yellow')
            continue

    # criando feredação e retornando
    return server.openFederated(repositories=lista_conexoes)


def conectar_repositorio(repositorio: str) -> RepositoryConnection:
    """
    Igual a `conectar()`, porém conecta somente no repositorio especificado.

    Se o repositório não existir, ele será criado.
    """

    checa_variavel_ambiente()

    server = AllegroGraphServer()           # servidor
    catalogo = server.openCatalog(None)     # catalogo root
    return catalogo.getRepository(
        name=repositorio,
        access_verb=Repository.ACCESS
    ).getConnection()


def obter_dicionario_completo(fed: RepositoryConnection) -> Dict[str, str]:
    """
    Obtem um dicionario contendo todas as produções no Allegro, na forma:

    { "Node": "texto_para_ser_usado_na_classificacao", ... }

    :param fed: Conexão com a federação
    :return: dicionario na forma acima
    """

    ret: Dict[str, str] = dict()

    # coletando producoes (exceto disciplinas)
    # producao é quando um objeto tem um título, e é do tipo bibo:Thesis, Article, Book ou Chapter
    with fed.executeTupleQuery(QUERY_PRODUCOES) as repository_result:       # fazendo a query
        for binding_set in repository_result:  # type: ListBindingSet       # iterando sobre os resultados
            ident: str = binding_set.getValue('ident').toNTriples()
            nome: str = binding_set.getValue('nome').toPython()
            ret[ident] = nome

    # coletando disciplinas
    with fed.executeTupleQuery(QUERY_DISCIPLINAS) as repository_result:
        for binding_set in repository_result:   # type: ListBindingSet
            ident: str = binding_set.getValue('ident').toNTriples()
            nome: str = binding_set.getValue('nome').toPython()
            ementa: str = binding_set.getValue('ementa').toPython()

            # verificando se a ementa contem algo importante para juntar com o nome da disciplina
            if "ementa" not in ementa.lower() and len(ementa) > 10:
                ret[ident] = f'{nome} {ementa}'
            else:
                ret[ident] = nome

    return ret


def obter_cad_puc_namespace(repo: RepositoryConnection) -> str | None:
    """
    Tenta obter o namespace de `cad-puc` em um repositorio.

    Caso não encontre, retorna None
    :param repo: Conexão com o repositório
    :return: URI do namespace, ou None
    """

    try:
        return repo.getNamespace('cad-puc')
    except RequestError:
        return None


def guardar_dicionario(
        repo: RepositoryConnection,
        dicionario: Dict[str, float],
        cad_puc_namespace=None
):
    """
    Armazena quais produções são relacionadas à meio ambiente no Allegro.

    Para cada produção, haverá uma tripla na seguinte forma:

        ```<Producao#id> <cad-puc:RelacionadoMeioAmbiente> NUMERO```

    Onde `NUMERO` é um número de 0 a 1, que diz o quão relacionado com meio ambiente.

    :param repo: Conexão com repositório a serem guardadas as triplas

    :param dicionario: Dicionario contendo as produções à serem inseridas. Deve ser no formato:
    { "Node": float, ... }

    :param cad_puc_namespace: Namespace para ser usado como `cad_puc`.
    Se não for definido, será usado "http://www.nima.puc-rio.br/cad-puc/"

    :return:
    """
    default_cad_puc_namespace = "http://www.nima.puc-rio.br/cad-puc/"

    if cad_puc_namespace is None:
        cprint(f'Namespace "cad-puc" nao definido, usando default: {default_cad_puc_namespace}', 'yellow')
        cad_puc_namespace = default_cad_puc_namespace

    predicado = repo.createURI(
        namespace=cad_puc_namespace,
        localname='RelacionadoMeioAmbiente'
    )

    # criando lista de triplas/statements a serem inseridas
    lista_triplas = [
        repo.createStatement(
            subject=node,
            predicate=predicado,
            object=repo.createLiteral(value=valor)
        )
        for node, valor in dicionario.items()
    ]

    # configurando batch size para serem 10 commits
    batch_size = len(lista_triplas) // 10
    cprint(f'Batch size: {batch_size}', 'blue')
    repo.add_commit_size = batch_size

    # adicionando no repositorio
    with repo.session():
        q = repo.size()
        repo.addTriples(triples_or_quads=lista_triplas)

        if repo.size() - q == len(lista_triplas):
            cprint('Operação efetuada com sucesso', 'green')
        else:
            cprint("Quantidade final não é a esperada. Efetuando rollback", 'red')
            repo.rollback()

    return


QUERY_PRODUCOES = """
    SELECT ?ident ?nome
    WHERE {
        ?ident 
            dc:title ?nome ;
            rdf:type ?tipo .
        filter (?tipo IN (
            <http://purl.org/ontology/bibo/Thesis>,
            <http://purl.org/ontology/bibo/Article>,
            <http://purl.org/ontology/bibo/Book>,
            <http://purl.org/ontology/bibo/Chapter>
        ) ) .    
    }
"""


QUERY_DISCIPLINAS = """
    PREFIX ccso: <https://w3id.org/ccso/ccso#>
    SELECT ?ident ?nome ?ementa
    WHERE {
        ?ident
            ccso:csName ?nome ;
            ccso:KnowledgeBody ?ementa .
    }
"""