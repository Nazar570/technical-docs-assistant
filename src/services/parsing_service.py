import logging
from pathlib import Path

from markitdown import MarkItDown

logger = logging.getLogger(__name__)


def parse_document_to_markdown(file_path: Path) -> str:
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    md = MarkItDown()
    logger.info(f"Parsing document: {file_path}")

    result = md.convert(str(file_path))
    return result.text_content
