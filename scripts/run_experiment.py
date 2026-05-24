import asyncio
import json
import os
from datetime import datetime

import httpx
import mlflow
import pandas as pd

MLFLOW_TRACKING_URI = "http://localhost:5000"
API_URL = "http://localhost:8000/api/v1/qa/ask"
TEST_QUERIES_PATH = "tests/evaluation/test_queries.json"

EXPERIMENT_CONFIG = {
    "top_k_retrieve": 20,
    "top_k_return": 5,
    "embedding_model": "BAAI/bge-small-en-v1.5",
    "reranker_model": "BAAI/bge-reranker-base",
    "llm_model": "gemini-1.5-flash",
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "retrieval_strategy": "Hybrid + RRF",
}


async def run_query(client: httpx.AsyncClient, query: str) -> dict:
    payload = {
        "query": query,
        "top_k_retrieve": EXPERIMENT_CONFIG["top_k_retrieve"],
        "top_k_return": EXPERIMENT_CONFIG["top_k_return"],
    }

    try:
        response = await client.post(API_URL, json=payload, timeout=30.0)
        response.raise_for_status()
        data = response.json()

        citations = [
            f"{c['chunk_id'][:8]} (Score: {c['rerank_score']:.2f})"
            for c in data.get("citations", [])
        ]

        return {
            "query": query,
            "answer": data["answer"],
            "citations": " | ".join(citations),
            "status": "success",
        }
    except Exception as e:
        return {"query": query, "answer": str(e), "citations": "", "status": "error"}


async def execute_experiment() -> None:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment("RAG_Baseline_Evaluations")

    with open(TEST_QUERIES_PATH, encoding="utf-8") as f:
        queries = json.load(f)

    print(f"Starting experiment run with {len(queries)} queries...")

    with mlflow.start_run(run_name=f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
        mlflow.log_params(EXPERIMENT_CONFIG)

        results = []
        success_count = 0

        async with httpx.AsyncClient() as client:
            for query in queries:
                print(f"Evaluating: {query}")
                result = await run_query(client, query)
                results.append(result)
                if result["status"] == "success":
                    success_count += 1

        mlflow.log_metric("total_queries", len(queries))
        mlflow.log_metric("successful_queries", success_count)
        mlflow.log_metric(
            "success_rate", success_count / len(queries) if queries else 0
        )

        df = pd.DataFrame(results)

        os.makedirs("local_data", exist_ok=True)
        artifact_path = "local_data/experiment_results.csv"
        df.to_csv(artifact_path, index=False)

        mlflow.log_param("results_csv_path", artifact_path)
        mlflow.log_metric("result_rows", len(df))

        print(f"\nExperiment complete. Success rate: {success_count}/{len(queries)}")
        print(f"Local results saved to: {artifact_path}")
        print(f"View results at: {MLFLOW_TRACKING_URI}")


if __name__ == "__main__":
    asyncio.run(execute_experiment())
