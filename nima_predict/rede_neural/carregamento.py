from keras.models import Sequential
from keras.models import load_model
import joblib
from sklearn.feature_extraction.text import CountVectorizer


def carregar_modelo(filename: str) -> Sequential:
    return load_model(filename)


def carregar_vectorizer(filename: str) -> CountVectorizer:
    return joblib.load(filename)

