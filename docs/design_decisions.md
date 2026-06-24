# DocuMind AI - Design Decisions & Engineering Choices

This document outlines key technical decisions made during the development of DocuMind AI, explaining the trade-offs and rationale.

## 1. Custom Text Splitter vs Heavy Libraries (e.g., LangChain)

**Decision**: Implemented a native, self-contained `RecursiveCharacterTextSplitter`.

**Rationale**:
- **Dependency Overhead**: Heavy libraries like LangChain pull in hundreds of transitive dependencies, leading to bloated Docker images, slow pipeline builds, and dependency conflicts.
- **Maintainability**: A custom splitter is transparent, easy to debug, and has a footprint of less than 120 lines of clean code while matching the behavior of standard langchain splitters.
- **Performance**: Native splitting using regex is fast and eliminates import-time latency.

---

## 2. SQLite for Telemetry Logging

**Decision**: Used SQLite (`observability/db_logger.py`) instead of standard server stdout logs or a heavy external database (e.g., PostgreSQL).

**Rationale**:
- **Structured Telemetry**: Standard print logs are hard to query. Using a lightweight relational database allows running queries on latency metrics, accuracy, and source hits.
- **Zero-Configuration**: SQLite is built into Python's standard library and writes to a single local file (`data/logs.db`), which matches the local development experience.
- **Persistence**: Unlike container standard logs, SQLite database files can be volume-mounted and persisted across server redeployments.

---

## 3. Dynamic BM25 Syncing

**Decision**: The `HybridRetriever` queries all documents currently in the vector store and builds the BM25 index on the fly, with lazy rebuilds when document counts change.

**Rationale**:
- **Single Source of Truth**: ChromaDB serves as the single source of truth for the entire corpus. We avoid syncing a second document store for BM25, preventing state drift.
- **Performance**: Building BM25 index over a localized document corpus of thousands of chunks takes less than 10 milliseconds, making on-the-fly construction extremely viable.
- **Dynamic Updates**: When new documents are uploaded via `/ingest`, the BM25 index updates automatically on the next query.

---

## 4. Offline Mock LLM Fallback

**Decision**: Added a local `MockLLM` that intercepts queries when OpenAI/Gemini API keys are absent.

**Rationale**:
- **CI/CD Compatibility**: Tests can run during automated build verification without requiring secret keys.
- **Resilience**: Prevents pipeline disruptions due to API rate limits, server downtime, or network failures.
- **Out-of-the-Box Setup**: Allows users checking out the repo for the first time to run health tests and sample queries instantly before configuring api keys.

---

## 5. Swappable Interfaces

**Decision**: Created abstract base classes for Embeddings (`vectorstore/base.py`) and LLMs (`llm/base.py`).

**Rationale**:
- **Provider Agility**: Easily switch from OpenAI to Gemini, Cohere, or local models (Ollama/Llama.cpp) without modifying API routes or retrieval flows.
- **Clean Separation of Concerns**: The FastAPI layers are completely decoupled from model API specifics.
