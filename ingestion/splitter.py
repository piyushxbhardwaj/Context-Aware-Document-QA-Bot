from typing import List
from ingestion.loaders import Document
from app.config import settings

class RecursiveCharacterTextSplitter:
    """
    Recursively splits text into chunks of specified size with overlap.
    A self-contained implementation mimicking standard RAG splitter logic.
    """
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        separators: List[str] = None
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.separators = separators or ["\n\n", "\n", " ", ""]
        
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                f"Chunk overlap ({self.chunk_overlap}) must be smaller than chunk size ({self.chunk_size})"
            )

    def split_text(self, text: str) -> List[str]:
        """Splits text into chunks of string."""
        return self._split_text(text, self.separators)

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        # If text is small enough, return it
        if len(text) <= self.chunk_size:
            return [text]

        # Find the best separator to use
        separator = separators[-1] if separators else ""
        new_separators = []
        for i, sep in enumerate(separators):
            if sep == "":
                separator = sep
                new_separators = separators[i+1:]
                break
            if sep in text:
                separator = sep
                new_separators = separators[i+1:]
                break

        # Split text
        if separator:
            splits = text.split(separator)
        else:
            splits = list(text)

        # Merge splits into chunks
        return self._merge_splits(splits, separator, new_separators)

    def _merge_splits(self, splits: List[str], separator: str, new_separators: List[str]) -> List[str]:
        chunks = []
        current_chunk = []
        current_length = 0

        for split in splits:
            split_len = len(split)
            sep_len = len(separator) if current_chunk else 0
            
            if current_length + split_len + sep_len <= self.chunk_size:
                current_chunk.append(split)
                current_length += split_len + sep_len
            else:
                if current_chunk:
                    chunks.append(separator.join(current_chunk))
                
                # If a single split is larger than chunk size, split it recursively
                if split_len > self.chunk_size:
                    sub_chunks = self._split_text(split, new_separators)
                    chunks.extend(sub_chunks)
                    current_chunk = []
                    current_length = 0
                else:
                    current_chunk = [split]
                    current_length = split_len

        if current_chunk:
            chunks.append(separator.join(current_chunk))

        # Re-merge/apply overlap using sliding window mechanism
        return self._apply_overlap(chunks)

    def _apply_overlap(self, chunks: List[str]) -> List[str]:
        if len(chunks) <= 1 or self.chunk_overlap <= 0:
            return chunks

        overlapped_chunks = []
        for i, chunk in enumerate(chunks):
            if i == 0:
                overlapped_chunks.append(chunk)
            else:
                prev_chunk = chunks[i - 1]
                # Calculate maximum allowed overlap characters so the combined chunk doesn't exceed self.chunk_size
                max_allowed_overlap = self.chunk_size - len(chunk) - 1
                effective_overlap = min(self.chunk_overlap, max_allowed_overlap)
                
                if effective_overlap > 0:
                    overlap_text = prev_chunk[-effective_overlap:]
                    # Align at word boundary if possible
                    if " " in overlap_text:
                        space_idx = overlap_text.find(" ")
                        overlap_text = overlap_text[space_idx + 1:]
                    
                    if overlap_text.strip():
                        overlapped_chunks.append(overlap_text + " " + chunk)
                    else:
                        overlapped_chunks.append(chunk)
                else:
                    overlapped_chunks.append(chunk)
        
        return overlapped_chunks

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Splits a list of Documents and creates new chunk Documents with metadata."""
        split_docs = []
        for doc in documents:
            chunks = self.split_text(doc.page_content)
            for i, chunk in enumerate(chunks):
                metadata = doc.metadata.copy()
                metadata["chunk_index"] = i
                split_docs.append(Document(page_content=chunk, metadata=metadata))
        return split_docs
