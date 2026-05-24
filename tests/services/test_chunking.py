from pathlib import Path

from src.services.chunking_service import chunk_markdown_file


def test_chunk_markdown_file(tmp_path: Path) -> None:
    md_content = """# Main Title
This is the introduction.

## Section 1
Here is some detail about section 1.
"""
    test_file = tmp_path / "test.md"
    test_file.write_text(md_content)

    chunks = chunk_markdown_file(test_file)

    assert len(chunks) > 0
    assert chunks[0]["metadata_json"].get("h1") == "Main Title"

    for chunk in chunks:
        assert "chunk_index" in chunk
        assert "text_content" in chunk
        assert "metadata_json" in chunk
