from typing import List

class BaseEmbeddings:
    """Base interface for embedding models to make them easily swappable."""
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of document strings."""
        raise NotImplementedError("Subclasses must implement embed_documents()")

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query string."""
        raise NotImplementedError("Subclasses must implement embed_query()")
