# NIMA Predict

**NIMA Predict** é uma ferramenta desenvolvida para determinar produções que estão relacionadas a *meio ambiente*.
A ferramenta foi desenvolvida para ser integrada no projeto [Busca@NIMA](http://buscanima.biobd.inf.puc-rio.br).

Essa ferramenta possui duas funcionalidades: 

* Classificação em **tempo real**: a ferramenta é um servidor que recebe produções e responde com sua classificação em
poucos milisegundos.
* Classificação **completa**: a ferramenta é um script que acessa o banco de dados e classifica todas as produções,
guardando no próprio banco de dados.


A classificação é feita através de uma rede neural, treinada sobre um conjunto de dados fornecido.

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


## Classificação em tempo real

Para rodar o servidor, execute o arquivo `main_tempo_real.py` em `nima_predict`, que utiliza três argumentos:

```shell
$ python nima_predict/main_tempo_real.py  PATH/PARA/MODELO  PATH/PARA/VETORIZADOR  PORTA_SERVIDOR
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
$ python main_tempo_real.py
```

Ou utilize `netcat` (em linux):

```shell
$ echo {"a": "b"} | nc 0.0.0.0 9999
```

## Classificação completa

O banco de dados para acessar e armazenar as produções é o [AllegroGraph](https://allegrograph.com/). Os dados 
das produções estão espalhados em diversos *repositórios* no banco. 

As queries SPARQL usadas para coletar as produções e as disciplinas são as seguintes.

```sparql

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

PREFIX ccso: <https://w3id.org/ccso/ccso#>
SELECT ?ident ?nome ?ementa
WHERE {
    ?ident
        ccso:csName ?nome ;
        ccso:KnowledgeBody ?ementa .
}

```

Para alterar as queries, edite as variáveis `QUERY_PRODUOES` e `QUERY_DISCIPLINAS`, no arquivo 
`nima_predict/classificacao/conexao.py`

Antes de executar o script, primeiro declare as seguintes variáveis de ambiente para serem usadas na conexão com o *AllegroGraph*:

```bash
$ export AGRAPH_HOST=localhost
$ export AGRAPH_PORT=10035
$ export AGRAPH_USER=seu_nome_de_usuario_aqui
$ export AGRAPH_PASSWORD=sua_senha_aqui
```

Feito isso, execute o arquivo `main_completo.py`:

```bash
$ cd nima_predict
$ python main_completo.py
```

Siga as instruções. Ele irá solicitar os arquivos da rede neural, assim como os nomes dos repositórios de onde ele irá
coletar todas as produções. No final, ele irá solicitar um repositório para armazenar as triplas resultantes