# Modular RAG with User Access Control

This project demonstrates two different strategies for implementing user-level access control in a Retrieval-Augmented Generation (RAG) system using LangChain, Ollama, and FastAPI.

## Prerequisites
- **Ollama**: Ensure Ollama is installed and running locally.
- **Models**:
  - LLM: `qwen2.5:0.5b` (`ollama pull qwen2.5:0.5b`)
  - Embeddings: `nomic-embed-text` (`ollama pull nomic-embed-text`)
- **Python**: 3.9+ with the provided `venv`.

---

## Strategy 1: Metadata-Level Filtering
Permissions are embedded directly into the vector database as metadata flags (e.g., `access_monish: True`).

### How it works:
1. **Ingestion**: Documents are chunked and tagged with boolean flags for each allowed user.
2. **Retrieval**: The database query includes a metadata filter to only return chunks the user is authorized to see.
3. **Generation**: Only authorized chunks reach the LLM.

### Pros/Cons:
- ✅ **Pros**: Efficient filtering at the database level; high security as unauthorized chunks never leave the DB.
- ❌ **Cons**: Requires re-indexing/re-populating the database if permissions change or new users are added.

### Usage:
```bash
# Ingest data
venv/bin/python "Strategy 1/ingest.py"

# Start server (Port 8000)
venv/bin/python "Strategy 1/main.py"

# Run tests
venv/bin/python "Strategy 1/test_api.py"
```

---

## Strategy 2: Post-Retrieval Filtering (CSV Mapping)
Permissions are decoupled from the database and managed via a central CSV file (`permissions.csv`).

### How it works:
1. **Ingestion**: Documents are stored with only the source filename in metadata.
2. **Retrieval**: The system retrieves the top N relevant chunks regardless of permissions.
3. **Filtering**: A Python middleware checks each chunk's source against the `permissions.csv` mapping and discards unauthorized ones.
4. **Generation**: The LLM receives only the remaining authorized chunks.

### Pros/Cons:
- ✅ **Pros**: Highly dynamic; update permissions instantly by editing the CSV without re-indexing.
- ❌ **Cons**: Slightly less efficient (retrieves chunks that might be discarded); potential for "empty" context if all top-N results are unauthorized.

### Usage:
```bash
# Ingest data
venv/bin/python "Strategy 2/ingest.py"

# Start server (Port 8001)
venv/bin/python "Strategy 2/main.py"

# Run tests
venv/bin/python "Strategy 2/test_api.py"
```

---

## Project Structure
- `data/`: Source PDF documents.
- `Strategy 1/`: Implementation of metadata-level filtering.
- `Strategy 2/`: Implementation of CSV-based post-retrieval filtering.
- `venv/`: Local Python environment.
- `README.md`: Project documentation.
