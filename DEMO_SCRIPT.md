# Loom Walkthrough - Video Demo Script (3-5 Minutes)

This script is structured to help you record a high-impact demo walkthrough of **DocuMind AI** for the ByteVox hiring team. It covers all core requirements, highlighting systems design, code quality, and engineering decisions.

---

## Part 1: Project & Architecture Overview (approx. 70 sec)

### 1. Introduction (20 sec)
* **What to Show**: Show the repository landing page on GitHub (with the embedded architecture diagram).
* **Talking Points**:
  > *"Hi, I'm Piyush Bhardwaj, and today I'm demonstrating DocuMind AI, a production-quality, context-aware document Q&A bot built with FastAPI, ChromaDB, and a custom hybrid retrieval pipeline. It's designed to ingestion-chunk PDF, Markdown, and TXT files and answer questions strictly constrained to the text, ensuring zero hallucinations."*

### 2. Project Folder Structure (20 sec)
* **What to Show**: Expand your VS Code folder tree.
* **Talking Points**:
  > *"The codebase is structured under clean architecture principles. We separate concerns into: `api` for endpoints, `ingestion` for loaders and text splitters, `vectorstore` for database connectivity, `retrieval` for dense/sparse/RRF search, `llm` for swappable provider clients, and `observability` for database query telemetry logging."*

### 3. Core Retrieval Architecture (30 sec)
* **What to Show**: Open `docs/architecture.md` showing the System Flow Diagram.
* **Talking Points**:
  > *"Instead of relying solely on semantic vector search, DocuMind AI implements Hybrid Retrieval. For every question, we query semantic matches via ChromaDB BGE embeddings (Dense Search) and lexical matches via BM25 (Sparse Search). We then merge these ranked lists using Reciprocal Rank Fusion (RRF) to retrieve highly relevant context blocks."*

---

## Part 2: Live Demo (approx. 140 sec)

### 4. Booting the Application (20 sec)
* **What to Show**: Open your terminal and run:
  `uvicorn api.main:app --reload`
* **Talking Points**:
  > *"I'll boot our FastAPI application locally using Uvicorn. The server starts instantly, establishing connections to our persistent ChromaDB collection and loading configuration variables from our environment."*

### 5. Swagger UI Exploration (20 sec)
* **What to Show**: Switch to your browser showing `http://127.0.0.1:8000/docs`.
* **Talking Points**:
  > *"FastAPI automatically exposes Swagger interactive docs at `/docs`. We see three endpoints: `/health` for system telemetry, `/ingest` for document processing, and `/query` for answering questions."*

### 6. Document Ingestion in Action (40 sec)
* **What to Show**: Use Swagger `/ingest` or curl to upload a document (e.g. `pricing.txt` or `setup.md`). Click "Execute" and show the JSON success response.
* **Talking Points**:
  > *"Let's ingest our pricing plan details. The file goes through our parser router, gets broken down into chunks using our character splitter, and is indexed in our vector store. We see the upload finished successfully, creating our database elements."*

### 7. Context-Aware Query Execution (40 sec)
* **What to Show**: Execute `/query` with the question:
  `{"question": "What pricing plan includes API access?"}`
  Show the returned answer, sources list (`["pricing.txt"]`), and latency.
* **Talking Points**:
  > *"Now I'll query: 'What pricing plan includes API access?'. The hybrid search locates the pricing context, fuses rankings, and feeds it to our LLM generator. We get a precise answer, correct source attribution, and latency metrics."*

### 8. Hallucination Prevention Guard (20 sec)
* **What to Show**: Execute `/query` with an unrelated question:
  `{"question": "Who won the FIFA World Cup in 2022?"}`
* **Talking Points**:
  > *"To verify our zero-hallucination guard, I'll ask an unrelated question about the FIFA World Cup. Because this facts-context is missing from our corpus, the LLM is strictly constrained and returns: 'This information is not available in the provided documents.'"*

---

## Part 3: Observability & Production scaling (approx. 90 sec)

### 9. Telemetry Logs & Evaluation (30 sec)
* **What to Show**: Open the SQLite database logs table or open `evaluation/report.md`.
* **Talking Points**:
  > *"Every query logs metadata—latency, content chunks, questions, and answers—to a local SQLite database for observability. We also have an automated evaluation framework that runs benchmark questions and outputs report summaries including hit rates and latency metrics."*

### 10. Production Scaling & Architecture (30 sec)
* **What to Show**: Open `docs/production_scaling.md` showing the Production Scaling Diagram.
* **Talking Points**:
  > *"To scale this application to 50,000 active users per day, we'd replace the local Chroma vector store with a distributed Qdrant or Milvus cluster, add NGINX rate-limiting load balancers, deploy FastAPI workers inside Kubernetes autoscaled containers, and configure Redis semantic query caching to optimize costs."*

### 11. Conclusion (30 sec)
* **What to Show**: Return to VS Code and show the `tests/` folder.
* **Talking Points**:
  > *"Key design decisions like a native character text splitter keep our dependencies lightweight, and the offline fallback modes ensure our CI/CD pipelines run without network disruptions. Thank you for reviewing DocuMind AI!"*
