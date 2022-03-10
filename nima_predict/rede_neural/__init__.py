from .treino import main as treinar
from .utilizacao import classificar
from .carregamento import carregar_modelo, carregar_vectorizer

__all__ = ["treinar", "classificar", "carregar_modelo", "carregar_vectorizer"]
