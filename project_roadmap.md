# mini-cursor-cli Roadmap

## Overview

This project implements a mini-version of Cursor's architecture, replicating their ingenious use of Merkle trees for incremental indexing, client-server communication, and AI-powered code interaction. Built to understand and learn from Cursor's engineering decisions described in [The Pragmatic Engineer article](https://newsletter.pragmaticengineer.com/p/cursor).

---

## Key Architecture (Based on Cursor's Design)

* **Client-Server Architecture**: CLI client maintains code locally, server handles indexing and LLM queries
* **Merkle Tree Sync**: Files as leaves, directories as nodes - efficient change detection
* **Dual Index System**: Merkle trees for change tracking + Vector database for semantic search  
* **Interactive Chat Loop**: Terminal-based conversation with your codebase
* **Agent Tools**: `read_file()`, `search_code()`, `edit_file()`, `list_files()` with colored diff output
* **Incremental Sync**: Compare client/server Merkle trees every 3 minutes, reindex only changes
* **Privacy-First**: Code never stored on server, only encrypted embeddings

---

## Business & Personal Objectives

1. **Reverse-engineer Cursor's architecture**: Learn how they achieve blazing-fast sync and search
2. **Master distributed indexing**: Build secure, incremental vector indexing from scratch
3. **AI Agent Engineering**: Implement tool-calling agents with rich terminal output
4. **Performance at Scale**: Handle large codebases efficiently using tree traversal algorithms
5. **End-to-end Implementation**: From file watching to LLM tool execution

---

## Learning Goals

* Merkle trees for distributed system synchronization
* Client-server communication patterns for AI applications  
* Vector embeddings and semantic search implementation
* Building interactive CLI applications with Rich
* LLM tool-calling and agent orchestration
* Tree traversal algorithms and hash-based change detection

---

## Delivery Roadmap

### Stage 1: Correct Merkle Tree Implementation ✅ (Refactor Current)

* **Goal:** Fix current implementation - files as leaves, directories as internal nodes
* **Current Issue:** Implemented chunks as leaves (wrong approach)
* **Deliverable:** 
  - `merkle/tree.py`: Files are leaves with content hash
  - `merkle/node.py`: Directories hash children recursively  
  - Unit tests for file/directory tree building
  - Tree comparison and diff detection methods

### Stage 2: Client-Server Foundation

* **Goal:** Set up client-server architecture with FastAPI backend
* **Deliverable:**
  - `agent/server.py`: FastAPI server for indexing and queries
  - `cli/client.py`: HTTP client for server communication
  - `cli/main.py`: Entry point and project detection
  - Basic health check and project registration endpoints

### Stage 3: Code Chunking & Vector Indexing (Server-Side)

* **Goal:** Server receives code, creates semantic chunks, generates embeddings
* **Deliverable:**
  - `agent/chunker.py`: Split files into ~500-token semantic chunks
  - `agent/embeddings.py`: OpenAI/local embedding generation
  - `agent/vector_db.py`: Store embeddings (Pinecone or local ChromaDB)
  - Server Merkle tree to track indexed state

### Stage 4: Incremental Sync System

* **Goal:** Client-server Merkle tree comparison for efficient reindexing
* **Deliverable:**
  - `cli/sync_engine.py`: Build local Merkle tree, compare with server
  - `agent/sync_handler.py`: Tree comparison and change detection
  - File watcher integration for real-time change detection
  - API endpoints: `POST /sync`, `POST /reindex`

### Stage 5: Interactive Chat Loop

* **Goal:** Terminal-based conversation interface like ChatGPT
* **Deliverable:**
  - `cli/chat.py`: Interactive REPL with Rich formatting
  - Conversation history and context management
  - Special commands: `/files`, `/sync`, `/status`, `/clear`
  - Graceful error handling and user experience

### Stage 6: Vector Search & Context Retrieval

* **Goal:** Semantic search to find relevant code chunks for queries
* **Deliverable:**
  - `agent/search.py`: Vector similarity search
  - `agent/context_builder.py`: Request specific code from client
  - API endpoint: `POST /query` with embedding-based search
  - Client code retrieval on-demand (never stored on server)

### Stage 7: Agent Tools Implementation

* **Goal:** Implement Cursor-style tools for code interaction
* **Deliverable:**
  - `agent/tools/read_file.py`: Read and display file contents
  - `agent/tools/search_code.py`: Search across codebase
  - `agent/tools/edit_file.py`: Apply code edits with validation  
  - `agent/tools/list_files.py`: Browse project structure
  - Tool validation and error handling

### Stage 8: LLM Integration & Tool Execution

* **Goal:** Orchestrate LLM with tool calls and response formatting
* **Deliverable:**
  - `agent/llm_client.py`: OpenAI/Claude integration with function calling
  - `agent/orchestrator.py`: Parse tool calls, execute, format responses
  - Rich terminal output: spinning indicators, colored diffs
  - Tool execution results: green additions, red deletions

### Stage 9: Advanced Features & Polish

* **Goal:** Add production-ready features and optimizations
* **Deliverable:**
  - `.cursorignore` support for sensitive files
  - Large codebase optimizations (selective indexing)
  - Error recovery and connection handling
  - Performance monitoring and logging
  - Configuration management

### Stage 10: Documentation & Demo

* **Goal:** Professional documentation with architecture diagrams
* **Deliverable:**
  - Comprehensive README with architecture explanation
  - Mermaid diagrams showing client-server flow
  - Demo video showing chat interaction and tool usage
  - Performance benchmarks vs naive approaches
  - Blog post about learnings from Cursor's architecture

---

## Technical Implementation Details

### Merkle Tree Structure (Corrected)
```
project/
├── src/                    Hash(main.py + utils.py)
│   ├── main.py            Hash(file content)
│   └── utils.py           Hash(file content)  
├── tests/                 Hash(test_main.py)
│   └── test_main.py       Hash(file content)
└── README.md              Hash(file content)

Root Hash = Hash(src/ + tests/ + README.md)
```

### Client-Server Communication Flow
```
1. Client builds local Merkle tree
2. POST /sync with tree structure  
3. Server compares with its tree
4. Returns list of changed files
5. Client sends changed file contents
6. Server reindexes only changes
7. User asks question in chat
8. Server does vector search
9. Server requests specific code from client
10. LLM processes with full context
```

### Agent Tools Output Format
```bash
👤 You: Add error handling to the login function

🤖 Mini Cursor: I'll add try-catch error handling to the login function.

🔧 Using tool: edit_file
📁 File: src/auth.py
📝 Changes:
- def login(email, password):
+ def login(email, password):
+     try:
+         # Login logic here
+     except ValidationError as e:
+         logger.error(f"Login failed: {e}")
+         raise

✅ File updated successfully!
```

---

*This roadmap now correctly implements Cursor's architecture: client-side code, server-side indexing, Merkle tree sync, and interactive AI tools with rich terminal output.*
