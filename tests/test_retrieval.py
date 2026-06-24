import pytest
from ingestion.loaders import Document
from retrieval.sparse import BM25Retriever
from retrieval.rrf import reciprocal_rank_fusion

def test_bm25_retriever():
    doc1 = Document(page_content="API access is included in the Enterprise plan.", metadata={"source": "doc1.txt"})
    doc2 = Document(page_content="The cancellation policy allows refunds within 14 days.", metadata={"source": "doc2.txt"})
    doc3 = Document(page_content="To set up the server run uvicorn api.main:app.", metadata={"source": "doc3.txt"})

    retriever = BM25Retriever([doc1, doc2, doc3])
    
    # Query matching doc1
    results = retriever.search_with_score("pricing plan API", limit=2)
    assert len(results) >= 1
    # Top result should be doc1
    assert results[0][0].metadata["source"] == "doc1.txt"

    # Query matching doc2
    results = retriever.search_with_score("cancellation refund dashboard", limit=2)
    assert len(results) >= 1
    assert results[0][0].metadata["source"] == "doc2.txt"

def test_reciprocal_rank_fusion():
    docA = Document(page_content="Document A content", metadata={"id": "A"})
    docB = Document(page_content="Document B content", metadata={"id": "B"})
    docC = Document(page_content="Document C content", metadata={"id": "C"})

    # Dense ranks: A first, B second
    dense_ranked = [docA, docB]
    # Sparse ranks: B first, C second
    sparse_ranked = [docB, docC]

    # RRF with k=60
    fused_results = reciprocal_rank_fusion([dense_ranked, sparse_ranked], k=60)

    # Document B is ranked 2nd in dense (rank 1 index) and 1st in sparse (rank 0 index)
    # Score for B: (1 / (60 + 2)) + (1 / (60 + 1)) = (1/62) + (1/61)
    # Score for A: (1 / (60 + 1)) = (1/61)
    # Score for C: (1 / (60 + 2)) = (1/62)
    
    # Doc B should have the highest score and rank first
    assert fused_results[0][0].metadata["id"] == "B"
    assert fused_results[1][0].metadata["id"] == "A"
    assert fused_results[2][0].metadata["id"] == "C"
