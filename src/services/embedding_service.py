import logging

from sentence_transformers import SentenceTransformer

from src.core.config import settings

logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    global _model

    if _model is None:
        logger.info(
            "Loading embedding model: %s",
            settings.embedding_model_name,
        )
        _model = SentenceTransformer(settings.embedding_model_name)

    return _model


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    model = get_embedding_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()
