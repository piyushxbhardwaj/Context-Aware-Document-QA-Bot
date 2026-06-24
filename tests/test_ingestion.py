import os
import pytest
from ingestion.loaders import TextLoader, Document
from ingestion.splitter import RecursiveCharacterTextSplitter

def test_text_loader(tmp_path):
    # Create temporary file
    temp_file = tmp_path / "sample.txt"
    content = "Hello DocuMind AI!\nThis is a sample document for unit testing."
    temp_file.write_text(content, encoding="utf-8")

    # Load file
    loader = TextLoader(str(temp_file))
    docs = loader.load()

    assert len(docs) == 1
    assert isinstance(docs[0], Document)
    assert docs[0].page_content == content
    assert docs[0].metadata["source"] == "sample.txt"
    assert docs[0].metadata["doc_type"] == "text"

def test_recursive_splitter():
    text = "Paragraph 1 is here.\n\nParagraph 2 is here. It is somewhat longer.\n\nParagraph 3 is here."
    # Set chunk size to fit individual paragraphs but not combined
    splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=10)
    chunks = splitter.split_text(text)

    assert len(chunks) >= 3
    for chunk in chunks:
        assert len(chunk) <= 50

def test_split_documents():
    doc = Document(
        page_content="Word1 Word2 Word3 Word4 Word5",
        metadata={"source": "test.txt", "doc_type": "text"}
    )
    # Extremely small chunk size to trigger splits
    splitter = RecursiveCharacterTextSplitter(chunk_size=15, chunk_overlap=2)
    split_docs = splitter.split_documents([doc])

    assert len(split_docs) > 1
    for i, split in enumerate(split_docs):
        assert split.metadata["source"] == "test.txt"
        assert split.metadata["chunk_index"] == i
        assert len(split.page_content) <= 15
