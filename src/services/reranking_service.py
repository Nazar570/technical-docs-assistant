import logging

from sentence_transformers import CrossEncoder

from src.core.config import settings

logger = logging.getLogger(__name__)

_reranker: CrossEncoder | None = None


def get_reranker() -> CrossEncoder:
    global _reranker

    if _reranker is None:
        logger.info(
            "Loading cross-encoder reranker model: %s",
            settings.reranker_model_name,
        )
        _reranker = CrossEncoder(
            settings.reranker_model_name,
            max_length=512,
        )

    return _reranker


def rerank_chunks(query: str, chunks: list[dict]) -> list[dict]:
    if not chunks:
        return []

    reranker = get_reranker()
    sentence_pairs = [[query, chunk["text_content"]] for chunk in chunks]
    scores = reranker.predict(sentence_pairs)

    for i, chunk in enumerate(chunks):
        chunk["rerank_score"] = float(scores[i])

    chunks.sort(key=lambda x: x["rerank_score"], reverse=True)
    return chunks
