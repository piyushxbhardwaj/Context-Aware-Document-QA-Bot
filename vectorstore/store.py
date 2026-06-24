import uuid
from typing import List, Tuple
import chromadb
from app.config import settings
from ingestion.loaders import Document
from vectorstore.base import BaseEmbeddings
from vectorstore.embeddings import ChromaEmbeddingFunctionWrapper

class ChromaVectorStore:
    """
    Manages connection to ChromaDB, document insertion, and similarity queries.
    Stores and retrieves chunk texts alongside source metadata.
    """
    def __init__(self, embedding_model: BaseEmbeddings, collection_name: str = "documind_collection"):
        self.embedding_model = embedding_model
        self.chroma_wrapper = ChromaEmbeddingFunctionWrapper(embedding_model)
        
        # Initialize Local Persistent Client
        self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.chroma_wrapper
        )

    def add_documents(self, documents: List[Document]) -> List[str]:
        """Inserts documents into ChromaDB, generating unique IDs."""
        if not documents:
            return []
            
        ids = [str(uuid.uuid4()) for _ in documents]
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        
        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )
        return ids

    def similarity_search_with_score(self, query: str, limit: int = None) -> List[Tuple[Document, float]]:
        """
        Query the vector store for dense matches.
        Returns a list of Tuple[Document, similarity_score].
        Higher score indicates higher similarity.
        """
        limit = limit or settings.TOP_K
        
        # Query ChromaDB collection
        results = self.collection.query(
            query_texts=[query],
            n_results=limit
        )
        
        output = []
        if not results or not results["documents"] or not results["documents"][0]:
            return output
            
        docs = results["documents"][0]
        metadatas = results["metadatas"][0] if results["metadatas"] else [{}] * len(docs)
        distances = results["distances"][0] if results["distances"] else [0.0] * len(docs)
        
        for doc_text, meta, dist in zip(docs, metadatas, distances):
            # Convert distance to a similarity score where higher is better
            # Cosine distance ranges [0, 2], L2 is [0, inf).
            # score = 1.0 / (1.0 + dist) is robust and handles all distance types
            similarity = 1.0 / (1.0 + dist)
            doc = Document(page_content=doc_text, metadata=meta)
            output.append((doc, similarity))
            
        return sorted(output, key=lambda x: x[1], reverse=True)

    def get_all_documents(self) -> List[Document]:
        """Retrieve all documents currently stored in the vector store."""
        results = self.collection.get()
        output = []
        if not results or not results["documents"]:
            return output
            
        docs = results["documents"]
        metadatas = results["metadatas"] if results["metadatas"] else [{}] * len(docs)
        for doc_text, meta in zip(docs, metadatas):
            output.append(Document(page_content=doc_text, metadata=meta))
        return output

    def reset(self):
        """Clears all stored documents in the vector store."""
        try:
            self.client.delete_collection(self.collection.name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection.name,
                embedding_function=self.chroma_wrapper
            )
        except Exception:
            pass
