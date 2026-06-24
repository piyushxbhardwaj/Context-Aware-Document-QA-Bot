from typing import List, Dict, Tuple
from ingestion.loaders import Document
from app.config import settings

def reciprocal_rank_fusion(
    ranked_lists: List[List[Document]],
    k: int = None
) -> List[Tuple[Document, float]]:
    """
    Fuses multiple ranked lists of Documents using the Reciprocal Rank Fusion algorithm.
    
    Formula:
        RRF_Score(d) = sum_{m in M} (1 / (k + rank_m(d)))
        where rank_m(d) is the 1-based index of document d in list m.
    """
    if k is None:
        k = settings.RRF_CONSTANT

    rrf_scores: Dict[str, float] = {}
    doc_map: Dict[str, Document] = {}

    for ranked_list in ranked_lists:
        for rank, doc in enumerate(ranked_list):
            # Use page content as deduplication key to combine match ranks
            key = doc.page_content.strip()
            
            # Keep the document with the most metadata if there are discrepancies
            if key not in doc_map or len(doc.metadata) > len(doc_map[key].metadata):
                doc_map[key] = doc
                
            # rank is 0-indexed, so 1-based rank is rank + 1
            score = 1.0 / (k + (rank + 1))
            rrf_scores[key] = rrf_scores.get(key, 0.0) + score

    # Sort documents by RRF score descending
    sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    return [(doc_map[key], score) for key, score in sorted_docs]
