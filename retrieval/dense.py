from typing import List, Tuple
from ingestion.loaders import Document
from vectorstore.store import ChromaVectorStore

class DenseRetriever:
    """
    Retrieves document chunks using semantic similarity via vector embeddings.
    """
    def __init__(self, vector_store: ChromaVectorStore):
        self.vector_store = vector_store

    def search_with_score(self, query: str, limit: int = 5) -> List[Tuple[Document, float]]:
        """Queries the underlying Chroma Vector Store."""
        return self.vector_store.similarity_search_with_score(query, limit=limit)
