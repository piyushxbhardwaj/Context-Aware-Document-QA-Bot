import os
import time
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.config import settings
from api.schemas import QueryRequest, QueryResponse, HealthResponse
from ingestion.parser import load_document
from ingestion.splitter import RecursiveCharacterTextSplitter
from vectorstore.embeddings import HuggingFaceBGEEmbeddings
from vectorstore.store import ChromaVectorStore
from retrieval.manager import HybridRetriever
from llm.generator import RAGGenerator

router = APIRouter()

# Lazy initialize core components to ensure FastAPI app starts quickly
_embeddings = None
_vector_store = None
_retriever = None
_generator = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceBGEEmbeddings()
    return _embeddings

def get_vector_store():
    global _vector_store
    if _vector_store is None:
        _vector_store = ChromaVectorStore(get_embeddings())
    return _vector_store

def get_retriever():
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever(get_vector_store())
    return _retriever

def get_generator():
    global _generator
    if _generator is None:
        _generator = RAGGenerator()
    return _generator

@router.get("/health", response_model=HealthResponse)
def health_check():
    """Returns the current state of the backend API."""
    return HealthResponse(
        status="healthy",
        details={
            "embeddings_model": settings.EMBEDDING_MODEL,
            "llm_provider": settings.LLM_PROVIDER,
            "chunk_size": settings.CHUNK_SIZE,
            "chunk_overlap": settings.CHUNK_OVERLAP
        }
    )

@router.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    """
    Uploads a document (PDF, Markdown, TXT) and processes it.
    It parses, chunks, and inserts it into the persistent vector database.
    """
    # Ensure temporary upload directory exists
    upload_dir = "data/documents"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    try:
        # Save uploaded file contents
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
            
        # Parse document into pages/elements
        documents = load_document(file_path)
        
        # Split documents using configurations
        splitter = RecursiveCharacterTextSplitter()
        chunks = splitter.split_documents(documents)
        
        # Store in ChromaDB vector store
        v_store = get_vector_store()
        v_store.add_documents(chunks)
        
        return {
            "message": "Ingestion successful",
            "filename": file.filename,
            "chunks_created": len(chunks),
            "original_pages": len(documents)
        }
    except Exception as e:
        # Clean up failed files if present
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Ingestion process failed: {str(e)}")

@router.post("/query", response_model=QueryResponse)
def query_bot(payload: QueryRequest):
    """
    Executes a user question against the context-aware hybrid retrieval RAG pipeline.
    Yields answer, attributed files, and latency.
    """
    start_time = time.time()
    try:
        # 1. Retrieve most relevant context chunks
        retriever_inst = get_retriever()
        retrieved_docs = retriever_inst.retrieve(payload.question)
        
        # 2. Feed retrieved chunks to LLM to formulate restricted response
        generator_inst = get_generator()
        answer, sources = generator_inst.generate_response(payload.question, retrieved_docs)
        
        # Calculate latency in ms
        latency_ms = int((time.time() - start_time) * 1000)
        
        # 3. Observability Logging (SQLite) - Safely try to log if module exists
        try:
            from observability.db_logger import SQLiteLogger
            # Format retrieved docs for logging
            formatted_docs = [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in retrieved_docs
            ]
            logger_db = SQLiteLogger()
            logger_db.log_query(
                query=payload.question,
                retrieved_chunks=formatted_docs,
                response=answer,
                latency_ms=latency_ms
            )
        except Exception as log_err:
            # We don't fail the user query if logging fails, but we print/log the warning
            import logging as py_logging
            py_logging.getLogger(__name__).warning(f"Could not log query telemetry to SQLite: {log_err}")
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            latency_ms=latency_ms
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")
