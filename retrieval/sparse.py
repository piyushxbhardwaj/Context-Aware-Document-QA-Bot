import re
from typing import List, Tuple
from rank_bm25 import BM25Okapi
from ingestion.loaders import Document

class BM25Retriever:
    """
    Sparse retriever using BM25 (Okapi) lexical search.
    Provides term-matching relevance scores for document chunks.
    """
    def __init__(self, documents: List[Document] = None):
        self.documents = documents or []
        self.bm25 = None
        if self.documents:
            self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenizer that lowercases and extracts alphanumeric words."""
        return re.findall(r'\w+', text.lower())

    def _build_index(self):
        """Constructs the BM25 index over the current corpus."""
        if not self.documents:
            self.bm25 = None
            return
        tokenized_corpus = [self._tokenize(doc.page_content) for doc in self.documents]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def update_documents(self, documents: List[Document]):
        """Re-builds BM25 index with a fresh list of documents."""
        self.documents = documents
        self._build_index()

    def search_with_score(self, query: str, limit: int = 5) -> List[Tuple[Document, float]]:
        """
        Queries the BM25 index.
        Returns a list of Tuple[Document, bm25_score] sorted descending by score.
        """
        if not self.documents or not self.bm25:
            return []
            
        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        
        # Zip documents with scores and filter out any with 0 score to reduce noise if needed,
        # but let's keep all and sort them so that everything gets ranked.
        results = list(zip(self.documents, scores))
        results_sorted = sorted(results, key=lambda x: x[1], reverse=True)
        
        return results_sorted[:limit]
