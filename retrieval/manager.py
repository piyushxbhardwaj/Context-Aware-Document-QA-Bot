from typing import List
from ingestion.loaders import Document
from vectorstore.store import ChromaVectorStore
from retrieval.dense import DenseRetriever
from retrieval.sparse import BM25Retriever
from retrieval.rrf import reciprocal_rank_fusion
from app.config import settings

class HybridRetriever:
    """
    Orchestrates Hybrid Retrieval by combining results from Dense vector search
    and Sparse keyword search (BM25) using Reciprocal Rank Fusion (RRF).
    """
    def __init__(self, vector_store: ChromaVectorStore):
        self.vector_store = vector_store
        self.dense_retriever = DenseRetriever(vector_store)
        self.sparse_retriever = BM25Retriever()
        self._last_doc_count = -1

    def _sync_sparse_index(self):
        """Retrieves all chunks from Chroma to sync the local BM25 vocabulary."""
        all_docs = self.vector_store.get_all_documents()
        if len(all_docs) != self._last_doc_count:
            self.sparse_retriever.update_documents(all_docs)
            self._last_doc_count = len(all_docs)

    def retrieve(self, query: str, limit: int = None) -> List[Document]:
        """
        Executes hybrid search and merges rankings via RRF.
        Returns the top-k final documents.
        """
        limit = limit or settings.TOP_K
        
        # Ensure BM25 has the latest index of all stored chunks
        self._sync_sparse_index()
        
        # If there are no documents in the database, return empty list
        if not self.sparse_retriever.documents:
            return []
            
        # Retrieve more than requested limit to allow RRF to select and rank well
        search_limit = max(limit * 3, 20)
        
        dense_results = self.dense_retriever.search_with_score(query, limit=search_limit)
        sparse_results = self.sparse_retriever.search_with_score(query, limit=search_limit)
        
        # Extract documents
        dense_docs = [doc for doc, _ in dense_results]
        sparse_docs = [doc for doc, _ in sparse_results]
        
        # Apply Reciprocal Rank Fusion
        fused = reciprocal_rank_fusion([dense_docs, sparse_docs])
        
        # Return the top-k documents
        return [doc for doc, _ in fused[:limit]]
