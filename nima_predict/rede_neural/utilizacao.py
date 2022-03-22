from collections import OrderedDict
from typing import Dict, List

import numpy as np
from keras.models import Sequential
from sklearn.feature_extraction.text import CountVectorizer


def _preparar_texto(lista_strings: List[str], vec: CountVectorizer):
    """Faz o processamento de texto, preparando para fazer a predição do texto"""
    return vec.transform(lista_strings)


def _converte_dicionario(dados: dict) -> OrderedDict:
    """
    Converte o dicionario em um dicionario

    O dicionario deve estar em alguma das três seguintes formas:

        1: {"ident": "texto" }   ou

        2: {"ident": ["texto1", "texto2", "texto3", ...] }   ou

        3: {"ident": {"nome": "texto1", "conteudo": "texto2" } }

    Caso esteja na forma 3, e não houver as chaves `nome` e `conteudo`, será
    levantada uma exceção `ValueError`

    Caso não esteja em nenhuma das três formas, será levantada uma exceção `TypeError`
    """

    # pegando um valor qualquer
    dados_convertidos = OrderedDict()
    for k, v in dados.items():
        if isinstance(v, str):                      # caso 1
            dados_convertidos[k] = v
        elif isinstance(v, list):                   # caso 2
            dados_convertidos[k] = " ".join(v)
        elif isinstance(v, dict):                   # caso 3
            if "nome" not in v or "conteudo" not in v:
                raise ValueError
            dados_convertidos[k] = f"{v['nome']} {v['conteudo']}"
        else:
            raise TypeError

    return dados_convertidos


def classificar(model: Sequential, vec: CountVectorizer, dados: Dict[str, str]) -> Dict[str, float]:
    """
    Faz uma predição usando o modelo treinado

    :param model: O modelo treinado

    :param vec: Um `CountVectorizer` treino nas sentenças

    :param dados: Um dicionario

    :return: um dicionario na forma { 'ident': {'conteudo': 'xxx...x', 'resultado': 0.23}, ... }
    """

    # convertendo os dados
    dados_convertidos = _converte_dicionario(dados)

    # faz a predição
    sentencas = vec.transform(list(dados_convertidos.values()))
    chaves = dados.keys()

    resultados = model.predict(
        x=sentencas,
        use_multiprocessing=True
    )

    # converte de volta
    dados_e_resultados = {
        chave: resultado.item()
        for chave, resultado in zip(chaves, np.nditer(resultados))
    }

    return dados_e_resultados

