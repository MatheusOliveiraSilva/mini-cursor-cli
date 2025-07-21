# mini-cursor-cli Roadmap

## Overview

The original Cursor IDE is built on a sophisticated set of AI Engineering features that I want to explore in this side project. This roadmap outlines what I want to build, why I’m building it, and what I aim to learn at each stage.

---

## Key Features

* **Merkle Tree Indexing**: manual implementation of Merkle trees over code chunks, using SHA-256 hashing.
* **Encrypted Embeddings on Pinecone**: generate embeddings, encrypt them locally, and upsert to Pinecone Free Tier.
* **Incremental Reindexing**: async file watcher to detect changes and keep the vector index up to date.
* **Chat-Driven CLI**: REPL using Typer + Rich for interacting with LLMs and showing tool invocations.
* **Agent Tools**:

  * `read_file(path)`
  * `search_code(query)`
  * `edit_file(path, diff)`
* **Colored Diff Output**: display removed lines in red and added lines in green via Rich.
* **Async Python 3.12**: leverage the latest async features (`asyncio`, `watchfiles`).

---

## Business & Personal Objectives

1. **Explore AI agent engineering**: learn how to map prompts, tools, and action execution in a loop.
2. **Master indexing pipelines**: build a secure, incremental index from scratch.
3. **Practice lean MLOps**: deploy with zero infrastructure cost using Pinecone free tier and local execution, simple CI/CD.
4. **Learn Rust (future phase)**: optionally enhance performance by integrating Rust modules.
5. **Demonstrate end-to-end capability**: showcase a prototype that goes from chunking code to agent-driven actions.

---

## Learning Goals

* Architecture of vector indexing systems and Merkle Trees.
* Implementing symmetric encryption to protect embeddings.
* Building interactive CLI applications with Rich and Typer.
* Developing LLM-driven agents with tool invocation.
* Orchestrating Pinecone as a vector database.
* CI/CD best practices with GitHub Actions and Docker.

---

## Delivery Roadmap

### Stage 1: Project Scaffold

* **Goal:** Set up project structure, dependencies, and basic tooling.
* **Deliverable:** Repository scaffold with folders (`indexer/`, `merkle/`, `cli/`, `agent/`), virtual environment config, and CI for linting.

### Stage 2: Merkle Tree Implementation

* **Goal:** Manually implement a Merkle Tree in Python using SHA-256.
* **Deliverable:** `merkle/` module with `add_leaf()`, `get_root()`, and unit tests for odd/even leaf counts.

### Stage 3: Code Chunking & Hashing

* **Goal:** Walk a code directory, split `.py` files into \~500-token chunks, hash each chunk, and feed the Merkle Tree.
* **Deliverable:** `indexer/chunk_and_hash.py` script producing JSON of `(file, chunk_index, hash)` entries.

### Stage 4: Embeddings & Pinecone Integration

* **Goal:** For each chunk, generate an embedding (OpenAI/Anthropic), encrypt with AES-GCM, and upsert to Pinecone.
* **Deliverable:** `indexer/pinecone_client.py` with `upsert_chunk(hash, encrypted_embedding)` and round-trip tests.

### Stage 5: Incremental Reindexing Job

* **Goal:** Use `watchfiles` to detect file creation/modification/deletion and update Pinecone accordingly.
* **Deliverable:** `indexer/watcher.py` script running in background with logs of operations.

### Stage 6: Basic Chat Shell CLI

* **Goal:** Build a REPL using Typer + Rich that accepts user prompts and displays raw LLM responses.
* **Deliverable:** `mini-cursor chat` command working without tool execution.

### Stage 7: Implement Agent Tools

* **Goal:** Define and implement internal tools: `read_file`, `search_code`, `edit_file`.
* **Deliverable:** `agent/tools.py` module with clear interfaces and integration tests.

### Stage 8: LLM + Tools Integration

* **Goal:** Develop `call_llm_and_tools(prompt)` to construct prompts, call LLM, parse JSON, execute tools, and collect diffs.
* **Deliverable:** CLI showing spinner and colored diffs (red/green) via Rich.

### Stage 9: CI/CD & Documentation

* **Goal:** Add Dockerfile and GitHub Actions workflows for lint, tests, and build; write comprehensive README with flow diagrams and demo GIF.
* **Deliverable:** Badges for build/test passing, Docker image, and polished documentation.

### Stage 10: Iterate & Polish

* **Goal:** Gather feedback, refine CLI UX, adjust chunk sizing, improve prompts, and add features (chat history, extra commands).
* **Deliverable:** v1.0 release with changelog and LinkedIn announcement.

---

*Each stage delivers a minimal viable component, building confidence and skills incrementally while keeping costs minimal.*
