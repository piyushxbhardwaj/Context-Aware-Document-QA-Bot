import os
from typing import List
from ingestion.loaders import Document, PDFLoader, MarkdownLoader, TextLoader

def load_document(file_path: str) -> List[Document]:
    """
    Unified entrypoint to load documents based on file extensions.
    Supports PDF, Markdown (.md), and plain text (.txt, .text).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        loader = PDFLoader(file_path)
    elif ext == ".md":
        loader = MarkdownLoader(file_path)
    elif ext in [".txt", ".text"]:
        loader = TextLoader(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {ext}. Supported extensions are: .pdf, .md, .txt, .text")
        
    return loader.load()
