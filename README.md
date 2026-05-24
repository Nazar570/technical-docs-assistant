# Technical Docs Assistant

Local-first RAG system that lets you upload internal technical documents and
ask natural language questions against them. The pipeline parses and chunks
files, embeds them with a sentence-transformer model, stores vectors in
Qdrant, and generates grounded answers via Gemini — citing the exact document
chunks it used so you can verify every claim.

## Stack

- **Document parsing**: pdfplumber, python-docx, markdown
- **Chunking**: recursive character splitter (configurable size / overlap)
- **Embeddings**: sentence-transformers (`all-MiniLM-L6-v2`)
- **Vector store**: Qdrant
- **Reranking**: cross-encoder (`ms-marco-MiniLM-L-6-v2`)
- **Search strategy**: hybrid retrieval (dense + BM25 via Elasticsearch)
- **Generation**: Google Gemini API
- **Primary database**: PostgreSQL + SQLAlchemy + Alembic
- **Cache**: Redis
- **Async worker**: Celery
- **API**: FastAPI + Uvicorn
- **Frontend**: Streamlit
- **Observability**: LLM tracing with Langfuse, metrics with Prometheus + Grafana
- **Orchestration**: Docker Compose
- **Quality**: ruff, ruff-format, pre-commit

## Setup

```bash
git clone https://github.com/Nazar570/technical-docs-assistant.git
cd technical-docs-assistant

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy and fill in your keys:

```bash
cp .env.example .env
# GEMINI_API_KEY=...
# LANGFUSE_PUBLIC_KEY=...
# LANGFUSE_SECRET_KEY=...
```

## Services

```bash
# Start all infrastructure (Postgres, Qdrant, Redis, Elasticsearch, Celery, Prometheus, Grafana)
docker compose up -d --build

docker compose logs -f
docker compose down
```

Apply database migrations:

```bash
alembic upgrade head
```

## Running the app

```bash
# API
uvicorn src.api.main:app --reload --port 8000

# Frontend (separate terminal)
streamlit run src/frontend/app.py
```

## Endpoints

- FastAPI docs: `http://localhost:8000/docs`
- Streamlit UI: `http://localhost:8501`
- Prometheus metrics: `http://localhost:9090`
- Grafana dashboards: `http://localhost:3000`
- `GET /health` — liveness check
- `POST /api/v1/documents/` — upload a document
- `GET /api/v1/documents/` — list all documents
- `POST /api/v1/qa/ask` — ask a question

```bash
curl -X POST http://localhost:8000/api/v1/qa/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the primary database?",
    "top_k_retrieve": 10,
    "top_k_return": 3,
    "score_threshold": 0.0
  }'
```

## Pipeline flow

```text
Upload file → Parse → Chunk → Embed → Index (Qdrant + Elasticsearch)
↓
Ask question → Hybrid retrieve → Rerank → Gemini → Grounded answer + citations
```

## Tests

```bash
make test
```

## Observability

All LLM calls are traced in Langfuse with input/output capture and latency
metadata. Prometheus scrapes `/metrics` from the FastAPI app; Grafana reads
from it to show generation latency and error counts.
