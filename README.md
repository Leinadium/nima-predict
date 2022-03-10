# NIMA Predict

Um pequeno servidor para classificar produções, determinado qual a probabilidade de ser relacionado 
à meio ambiente ou não.

Essa classificação é feita através de uma rede neural, treinada sobre um conjunto de dados.

## Preparação

### Dados

Primeiro, tenha em mãos um conjunto de dados, na seguinte estrutura, para treinar a rede neural:

```
| ident    | nome                          | tipo       | conteudo                | res   |
|----------|-------------------------------|------------|-------------------------|-------|
| abcd1234 | Ensaios sobre justiça         | Livro      | -                       | False |
| jkla9367 | Modelagem Geométrica          | Artigo     | -                       | False |
| apbi4638 | Organismos Fotossintetizantes | Disciplina | Origem e diversidade... | True  |
```

Em que `ident` seria um identificador, o `nome` contém o nome da produção, o `tipo` é um classificador genérico 
da produção, o `conteudo` contém alguma descrição geral da produção, e `res` diz se é relacionado a meio ambiente 
ou não.

### Ambiente Virtual

É altamente recomendo a utilização de um ambiente virtual em Python, ou usar algum gerenciador de ambientes como o 
[conda](https://docs.conda.io/en/latest/miniconda.html). Abaixo estão as instruções de como gerar um ambiente virtual
utilizando o *venv* :

```shell
# criando o ambiente virtual em "venv"
$ python -m venv venv

# iniciando o ambiente virtual
# windows
$ venv\Scripts\activate
# mac/linux
$ ./venv/Scripts/activate

# saindo do ambiente virtual
$ deactivate
```

Depois disso, instale os pacotes necessários:

```shell
# windows
(venv) $ pip install -r requirements.txt
# mac/linux
(venv) $ pip3 install -r requirements.txt
```

### Treinamento

Para treinar o modelo de rede neural, execute a função `main` dentro de `nima_predict.rede_neural.treino` :

```shell
$ cd nima_predict
$ python    # python3 se mac/linux

>>> from rede_neural import treino
>>> treino.main()
```

Siga as instruções, e ele irá gerar um arquivo *.h* (o modelo de rede neural) e um arquivo *.pkl* (um vetorizador, para
o pré tratamento das palavras)


## Utilização

Para rodar o servidor, execute o arquivo `main.py` em `nima_predict`, que utiliza três argumentos:

```shell
$ python nima_predict/main.py  PATH/PARA/MODELO  PATH/PARA/VETORIZADOR  PORTA_SERVIDOR
```

O servidor espera receber um *JSON* em alguma das seguintes três formas:

```json
{
  "identificador_1": "TEXTO PARA SER CLASSIFICADO",
  "identificador_2": ["PARTES", "DE", "UM TEXTO", "PARA", "SER CONCATENADO", "E CLASSIFICADO"],
  "identificador_3": {
    "nome": "nome da produção", "conteudo": "conteudo da produção"
  }
}
```

e irá responder com a chance de ser de meio ambiente:

```json
{
  "identificador_1": 0.123,
  "identificador_2": 0.234
}
```

Para testar, execute o script `exemplo/main.py`, que envia o conteudo de `/exemplo/data.json`

```shell
$ cd exemplo
$ python main.py
```

Ou utilize `netcat` (em linux):

```shell
$ echo {"a": "b"} | nc 0.0.0.0 9999
```