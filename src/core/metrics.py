from prometheus_client import Counter, Histogram

RAG_RETRIEVAL_LATENCY = Histogram(
    "rag_retrieval_seconds",
    "Time spent executing hybrid retrieval and reranking",
)

LLM_GENERATION_LATENCY = Histogram(
    "llm_generation_seconds",
    "Time spent waiting for the Gemini API to generate an answer",
)

LLM_ERROR_COUNT = Counter(
    "llm_generation_errors_total",
    "Total number of failed API calls to the LLM provider",
)

DOCUMENT_UPLOAD_COUNT = Counter(
    "document_uploads_total",
    "Total number of documents submitted for processing",
)
