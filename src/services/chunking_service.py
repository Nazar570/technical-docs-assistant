import logging
from pathlib import Path

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

logger = logging.getLogger(__name__)


def chunk_markdown_file(
    file_path: Path,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[dict]:
    """
    Reads a markdown file and chunks it semantically based on headers,
    falling back to character splitting for long sections.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {file_path}")

    text = file_path.read_text(encoding="utf-8")

    headers_to_split_on = [
        ("#", "h1"),
        ("##", "h2"),
        ("###", "h3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on
    )
    md_header_splits = markdown_splitter.split_text(text)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )

    final_splits = text_splitter.split_documents(md_header_splits)

    chunks = []
    for i, doc in enumerate(final_splits):
        chunks.append(
            {
                "chunk_index": i,
                "text_content": doc.page_content,
                "metadata_json": doc.metadata,
            }
        )

    logger.info(
        "Generated %s chunks from %s",
        len(chunks),
        file_path.name,
    )
    return chunks
