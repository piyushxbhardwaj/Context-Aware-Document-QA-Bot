# ByteVox Hybrid RAG - Interview Preparation Guide

This guide compiles critical technical questions, suggested answers, design trade-offs, and architecture explanations based on our evaluation of the Nexus AI Hybrid RAG pipeline. Use this to prepare for discussions with the ByteVox engineering team.

---

## 1. Core Architecture & Design Decisions

### Q: Why did you choose a Hybrid Retrieval system (Dense + Sparse) rather than a pure Vector database?
* **Answer**: In a production enterprise setting, user queries are highly diverse. 
  - **Dense vector retrieval** handles semantic queries, synonyms, and natural language phrasing well by embedding text in a vector space. However, it struggles with **exact keyword matches, model numbers, version strings, API endpoints, and specific error codes (like exit code 137 or v3.2.0)** because vector embeddings tend to abstract away specific character sequences.
  - **Sparse lexical retrieval (BM25)** is exceptionally good at finding exact word matches, codes, and method names, but has zero semantic understanding.
  - By combining them via **Reciprocal Rank Fusion (RRF)**, we get the best of both worlds. The evaluation report shows that dense retrieval was crucial for security white paper questions, whereas BM25 was mandatory to find troubleshooting sections matching the specific error code `137`.

### Q: What is Reciprocal Rank Fusion (RRF) and how does it combine rankings?
* **Answer**: RRF is a rank-based fusion algorithm. Instead of trying to normalize and combine raw scores (which is difficult because dense similarity scores and BM25 scores are on completely different scales and distributions), RRF uses the **ranks** of the documents in each list.
* The formula is:
  $$RRF\_Score(d) = \sum_{m \in M} \frac{1}{k + rank_m(d)}$$
  where $rank_m(d)$ is the 1-based rank of document $d$ in retriever $m$, and $k$ is a smoothing constant (typically set to 60). This penalizes documents that appear very low in the lists while heavily rewarding documents that appear near the top of either list. It is robust, parameter-light, and guarantees that highly relevant documents from either retriever bubble up to the top.

### Q: How is the vector database synchronized with the sparse BM25 retriever?
* **Answer**: In our architecture, **ChromaDB** is the single source of truth for all chunks. Since BM25 requires a global vocabulary index to compute IDF (Inverse Document Frequency), we implemented a synchronization wrapper in `retriever/manager.py` (`_sync_sparse_index`). When a retrieval is requested, the manager checks if the total chunk count in Chroma matches the local BM25 corpus count. If they mismatch, it fetches all stored documents from Chroma and rebuilds the BM25 index. This ensures the keyword vocabulary remains perfectly aligned.

---

## 2. Ingestion & Retrieval Quality Tuning

### Q: What chunking strategy did you select and why?
* **Answer**: We utilized a `RecursiveCharacterTextSplitter` with `chunk_size = 500` characters and `chunk_overlap = 100` characters. 
  - A chunk size of 500 characters is optimal for developer documentation because it is large enough to contain complete paragraphs, API endpoint schemas, or small code snippets (roughly 70–100 words), while small enough to avoid dilute contexts.
  - An overlap of 100 characters ensures that sentences or code declarations split at chunk boundaries have their preceding context carried over, preventing retrieval failures on terms split in half.

### Q: How did you verify and prevent hallucinations?
* **Answer**: Hallucinations are the largest risk in RAG pipelines. We enforced three layers of defense:
  1. **Source Context Restriction**: The system prompt strictly forces the LLM to only answer using the provided context blocks.
  2. **Explicit Refusal Instruction**: The prompt mandates returning exactly *"This information is not available in the provided documents."* if the context does not contain the answer, forbidding external knowledge.
  3. **Low-Similarity Rejection**: If no documents are retrieved (or their similarity scores are near zero), the RAG generator refuses immediately without invoking the LLM, saving inference cost and preventing hallucination.
  - In our testing of 10 completely out-of-scope questions, the system achieved **100% refusal compliance**.

---

## 3. Engineering Trade-Offs

### Q: What are the trade-offs of storing BM25 index in memory vs using a dedicated search engine?
| Option | Pros | Cons | Best For |
| :--- | :--- | :--- | :--- |
| **In-Memory BM25 (current)** | Zero infrastructure overhead, fast local lookups, single database deployment | Index scales with memory, slow startup when fetching all chunks to rebuild index | Smaller corpora ($\le 50,000$ chunks), local CLI bots, microservices |
| **Elasticsearch / Opensearch** | Scales to millions of docs, handles text highlighting, synonym mapping, native BM25 | Adds heavy infrastructure overhead, requires syncing databases, high server cost | Large-scale enterprise systems, multi-developer teams |

### Q: How would you scale this RAG pipeline to handle 10,000 concurrent requests?
* **Answer**: To scale this system in production:
  1. **Caching**: Implement a Redis cache for query-to-response mapping (already configured in config settings). Frequently asked questions (e.g. "What is your pricing?") bypass retrieval and generation entirely.
  2. **Horizontal Scaling of FastAPI**: Run FastAPI in multiple Kubernetes pods behind an Ingress controller, managed by an autoscaler.
  3. **Vector DB Scaling**: Move from a local Chroma DB persistent folder to a managed cluster vector database like Milvus, Qdrant, or Pinecone to support fast distributed similarity search.
  4. **Embedding Batching**: Use a dedicated Triton Server or TEI (Text Embeddings Inference) with batching enabled to handle concurrent embedding requests efficiently.
  5. **Asynchronous LLM calls**: Use async client calls in FastAPI to release the event loop while waiting for LLM generation.
