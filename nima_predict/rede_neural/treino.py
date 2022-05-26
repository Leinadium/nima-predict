import pandas as pd
from keras.models import Sequential
from pandas import DataFrame
import joblib
from typing import Tuple, Set


def _ler_arquivo(filename: str) -> DataFrame:
    """
    Le o arquivo, e converte para um DataFrame.

    Também adiciona um campo `sentence` no DataFrame

    :param filename: path para o arquivo csv

    :return: Um objeto `DataFrame`
    """

    df: DataFrame = pd.read_csv(
        filepath_or_buffer=filename,
        header=0,
        sep=','
    )
    df["sentence"] = ""

    return df


def _coletar_stopwords() -> Set[str]:
    """
    Coleta stopwords tanto em ingles como em portugues

    :return: Um `Set` com as stopwords em string
    """

    import nltk
    from unidecode import unidecode

    # baixando as stopwords
    nltk.download('stopwords')

    palavras_ingles: set = set(nltk.corpus.stopwords.words('english'))
    palavras_portugues: set = set(nltk.corpus.stopwords.words('portuguese'))

    palavras_portugues_niveladas: set = {unidecode(x) for x in palavras_portugues}

    palavras_juntas: set = palavras_ingles.union(palavras_portugues_niveladas)
    return palavras_juntas


def _preprocessamento_dados_para_sentenca(df: DataFrame):
    """
    Coloca na coluna "sentence" o nome com concatenado com o conteudo.
    Se for uma disciplina com uma ementa válida

    :param df: objeto `DataFrame`

    :return: None
    """
    def eh_valido(e: str) -> bool: return "ementa" not in e.lower() and len(e) > 10

    for index in df.index:
        nome = df.loc[index, 'nome']            # nome
        conteudo = df.loc[index, 'conteudo']    # conteudo
        tipo = df.loc[index, 'tipo']            # tipo
        # concatena nome com conteudo,  se conteudo nao tiver a palavra "ementa" e for uma disciplina
        # isso acontece quando uma producao
        sentenca = f'{nome} {conteudo if (tipo == "Course" and eh_valido(conteudo)) else ""}'
        df.loc[index, 'sentence'] = sentenca

    return


def _separar_treino_teste(df: DataFrame) -> Tuple:
    """
    Separa o dataframe em 4 conjuntos: duas contendo a parte de testes, e outras duas para os treinos

    :param df: objeto `DataFrame`

    :return: Um objeto `Dados`, contendo as 4 listas
    """
    from sklearn.model_selection import train_test_split

    # separando para testes e para treino
    sentencas = df['sentence'].values
    res = df['res'].values

    return train_test_split(sentencas, res, test_size=0.2, random_state=123)


def _bag_of_words(sentencas_treino, sentencas_teste, filename: str) -> Tuple:
    """
    Aplica o CountVector, que transforma o texto em uma matriz esparsa

    Retorna um novo `Dados`.

    Também armazena o `Vectorizer` criado

    :param sentencas_treino: lista de sentencas para treino

    :param sentencas_teste: lista de sentencas para teste

    :return: as listas transformadas em matrizes esparsas
    """

    from sklearn.feature_extraction.text import CountVectorizer

    vectorizer = CountVectorizer(
        strip_accents='unicode',                # normaliza
        lowercase=True,                         # converte para minuscula
        stop_words=list(_coletar_stopwords())    # retira as stopwords
    )

    vectorizer.fit(sentencas_treino)            # inicia o dicionario interno para a matriz esparsa

    joblib.dump(vectorizer, filename)

    # transformando
    sentencas_treino_vec = vectorizer.transform(sentencas_treino)
    sentencas_teste_vec = vectorizer.transform(sentencas_teste)

    return sentencas_treino_vec, sentencas_teste_vec


def _gerar_rede_neural(x_treino, x_teste, res_treino, res_teste) -> Sequential:
    from keras import layers
    from keras.backend import clear_session
    from tensorflow import random
    random.set_seed(123)

    clear_session()

    # numero de features
    input_dim = x_treino.shape[1]       # exemplo: (quantidade: 944, bow: 4300)

    model = Sequential()
    model.add(layers.Dense(50, input_dim=input_dim, activation='relu'))
    model.add(layers.Dense(70, input_dim=input_dim, activation='relu'))
    # model.add(layers.Dropout(rate=.2, input_dim=input_dim))
    model.add(layers.Dense(20, input_dim=input_dim, activation='relu'))
    model.add(layers.Dense(1, activation='sigmoid'))

    model.compile(
        loss='binary_crossentropy',
        optimizer='adam',
        metrics=['accuracy']
    )

    # treino
    _history = model.fit(
        x=x_treino,
        y=res_treino,
        epochs=30,
        verbose=False,
        validation_data=(x_teste, res_teste),
        batch_size=50
    )

    # print(history.history.keys())

    print("Neural network (sequential) usando keras")
    _, accuracy = model.evaluate(x_treino, res_treino, verbose=False)
    print("Training accuracy: {:.4}".format(accuracy))
    _, accuracy = model.evaluate(x_teste, res_teste, verbose=False)
    print("Training accuracy: {:.4}".format(accuracy))

    return model


def _salva_rede_neural(model: Sequential, filename: str):
    model.save(
        filepath=filename,
        overwrite=True,
        save_format='h5'
    )


def main():
    try:
        print("Lendo o dataFrame:")
        fn = input("  Digite o nome de arquivo de dados: ")
        dataframe = _ler_arquivo(fn)
        print("  Lido dataFrame")

        print("Processando os dados: ")
        _preprocessamento_dados_para_sentenca(dataframe)

        # separando
        print("  Seperando para teste e treino")
        dados = _separar_treino_teste(dataframe)

        # transforma
        print("  Aplicando B. O. W.")
        fn = input("  Digite o nome do arquivo para armazenar o Vectorizer: ")
        vecs = _bag_of_words(dados[0], dados[1], fn)

        # criando modelo
        print("Criando modelo")
        modelo = _gerar_rede_neural(
            x_treino=vecs[0],
            x_teste=vecs[1],
            res_treino=dados[2],
            res_teste=dados[3]
        )

        # salvando modelo
        print("Salvando modelo: ")
        fn_out = input("  Digite o nome de arquivo de saida (.h): ")
        _salva_rede_neural(modelo, fn_out)

    except FileNotFoundError:
        print("Arquivo nao encontrado. Tente novamente")

    except Exception as e:
        print("Erro: ", e)


main()
