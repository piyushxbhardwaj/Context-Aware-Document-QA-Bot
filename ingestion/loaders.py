import os
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from pypdf import PdfReader

class Document(BaseModel):
    """Unified Document schema used throughout the ingestion and retrieval pipeline."""
    page_content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BaseLoader:
    """Base class for all document loaders."""
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self) -> List[Document]:
        raise NotImplementedError("Subclasses must implement load()")

class PDFLoader(BaseLoader):
    """Loads PDF files page-by-page extracting text and page number metadata."""
    def load(self) -> List[Document]:
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        filename = os.path.basename(self.file_path)
        documents = []
        try:
            reader = PdfReader(self.file_path)
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                text = text.strip()
                if text:
                    metadata = {
                        "source": filename,
                        "doc_type": "pdf",
                        "page_number": i + 1
                    }
                    documents.append(Document(page_content=text, metadata=metadata))
        except Exception as e:
            raise RuntimeError(f"Error reading PDF file {self.file_path}: {e}")
        return documents

class MarkdownLoader(BaseLoader):
    """Loads Markdown files as a single document."""
    def load(self) -> List[Document]:
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        filename = os.path.basename(self.file_path)
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                text = f.read().strip()
            
            metadata = {
                "source": filename,
                "doc_type": "markdown"
            }
            return [Document(page_content=text, metadata=metadata)]
        except Exception as e:
            raise RuntimeError(f"Error reading Markdown file {self.file_path}: {e}")

class TextLoader(BaseLoader):
    """Loads plain text files as a single document."""
    def load(self) -> List[Document]:
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        filename = os.path.basename(self.file_path)
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                text = f.read().strip()
            
            metadata = {
                "source": filename,
                "doc_type": "text"
            }
            return [Document(page_content=text, metadata=metadata)]
        except Exception as e:
            raise RuntimeError(f"Error reading text file {self.file_path}: {e}")
