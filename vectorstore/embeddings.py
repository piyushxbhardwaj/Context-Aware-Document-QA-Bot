from typing import List
from sentence_transformers import SentenceTransformer
from vectorstore.base import BaseEmbeddings
from app.config import settings
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

class HuggingFaceBGEEmbeddings(BaseEmbeddings):
    """
    HuggingFace BAAI/bge-small-en-v1.5 embedding model implementation.
    """
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        # Lazy load model to avoid importing errors before pip install finishes
        self._model = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # BGE v1.5 works well without prefix for documents
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        # BGE recommendation: Represent query for retrieval
        prefix = "Represent this sentence for searching relevant passages: "
        embedding = self.model.encode(prefix + text, show_progress_bar=False)
        return embedding.tolist()

class ChromaEmbeddingFunctionWrapper(EmbeddingFunction):
    """
    Wrapper to make our BaseEmbeddings compatible with ChromaDB's embedding function interface.
    """
    def __init__(self, embeddings_model: BaseEmbeddings):
        self.embeddings_model = embeddings_model

    def __call__(self, input: Documents) -> Embeddings:
        # ChromaDB expects a list of embeddings for documents
        return self.embeddings_model.embed_documents(list(input))
