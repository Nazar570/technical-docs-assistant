import logging

import google.generativeai as genai
from fastapi import HTTPException, status
from langfuse.decorators import langfuse_context, observe

from src.core.config import settings
from src.core.metrics import LLM_ERROR_COUNT, LLM_GENERATION_LATENCY
from src.schemas.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)


@LLM_GENERATION_LATENCY.time()
@observe(as_type="generation", name="gemini_grounded_generation")
def generate_grounded_answer(query: str, chunks: list[RetrievedChunk]) -> str:
    if not settings.gemini_api_key:
        logger.error("GEMINI_API_KEY is not configured.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LLM API key is not configured.",
        )

    if not chunks:
        return "I could not find any relevant documents to answer your question."

    genai.configure(api_key=settings.gemini_api_key)

    context_parts = []
    for chunk in chunks:
        context_parts.append(
            f"--- Document ID: {chunk.chunk_id} ---\n{chunk.text_content}\n"
        )

    context_string = "\n".join(context_parts)

    system_instruction = (
        "You are a professional technical assistant. You must answer "
        "the user's question using ONLY the information provided in "
        "the Context below.\n"
        "If the answer cannot be found in the Context, state exactly: "
        "'I cannot answer this based on the provided documents.'\n"
        "Do not use outside knowledge. Do not hallucinate.\n"
        "When you state a fact from the context, cite the Document ID "
        "inline, for example: [Doc 123e4567-...]."
    )

    prompt = f"Context:\n{context_string}\n\nQuestion: {query}"

    langfuse_context.update_current_observation(
        input={"system": system_instruction, "user": prompt},
        model=settings.llm_model_name,
    )

    try:
        model = genai.GenerativeModel(
            model_name=settings.llm_model_name,
            system_instruction=system_instruction,
            generation_config=genai.GenerationConfig(
                temperature=settings.generation_temperature,
            ),
        )

        response = model.generate_content(prompt)
        answer = response.text.strip()

        langfuse_context.update_current_observation(output=answer)

        return answer

    except Exception as e:
        LLM_ERROR_COUNT.inc()
        logger.exception("Failed to generate answer from Gemini API.")
        langfuse_context.update_current_observation(
            level="ERROR", status_message=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error communicating with the generation model.",
        )
