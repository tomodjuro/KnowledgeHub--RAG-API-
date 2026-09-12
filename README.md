[![CI Pipeline](https://github.com/tomodjuro/KnowledgeHub--RAG-API-/actions/workflows/ci.yml/badge.svg)](https://github.com/tomodjuro/KnowledgeHub--RAG-API-/actions)


# KnowledgeHub API (RAG API)


[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0+-009688.svg)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-Modular-121212.svg)](https://www.langchain.com/)
[![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-purple.svg)](https://www.trychroma.com/)
[![Groq](https://img.shields.io/badge/LLM-Groq%20API-orange.svg)](https://groq.com/)

> An asynchronous Retrieval-Augmented Generation (RAG) API built with FastAPI, LangChain, ChromaDB, and Groq LLM for intelligent document querying across enterprise file formats.

---

### Overview

Imagine joining a new company where all guidelines, rules, code, and documentation are scattered across hundreds of different files and formats. Instead of spending days hunting down the right information or constantly interrupting colleagues, this project creates a smart technical assistant for the team.

**What the project does:**

* **Collects and Reads Documents:** Automatically processes all internal technical documentation and code.
* **Identifies Key Insights:** Breaks those documents down into smaller chunks and stores them in its "smart memory" (a vector database).
* **Answers Questions with Proof:** When asked a question (e.g., "How do we run this service?" or "What does this function do?"), the assistant instantly retrieves the exact relevant excerpts, analyzes them, and delivers a clear answer in English or Croatian—along with precise source citations referencing where the information was extracted.

---

### Key Features

* **Multi-Format Document Ingestion**: Native support for `.md`, `.txt`, `.pdf`, `.docx` (Word), and `.xlsx` (Excel).
* **Asynchronous Processing**: Non-blocking ingestion pipeline using FastAPI `BackgroundTasks` (returns `202 Accepted` immediately).
* **Incremental Reindexing**: Batch processing via `/api/v1/reindex` for directory-wide document syncing.
* **Enterprise-Grade Vector Search**: Embeddings powered by `sentence-transformers/all-MiniLM-L6-v2` with persistent vector storage in `ChromaDB`.
* **Fast LLM Inference**: Integration with Groq API (`openai/gpt-oss-120b`) for rapid context-aware responses.

---

### Tech Stack

| Component | Technology |
| :--- | :--- |
| **Framework** | FastAPI (Python 3) |
| **Orchestration** | LangChain (Modular architecture) |
| **Vector Database** | ChromaDB |
| **Embedding Model** | `sentence-transformers/all-MiniLM-L6-v2` (HuggingFace) |
| **LLM** | Groq API (`openai/gpt-oss-120b`) |
| **Parsers & Utilities** | `pypdf`, `python-docx`, `pandas`, `openpyxl`, `python-multipart` |

---

### Architecture Overview

1. **Upload / Reindex**: Incoming documents are saved to `./docs` and dispatched to background workers.
2. **Parsing & Chunking**: Documents are parsed by format-specific loaders (`TextLoader`, `PyPDFLoader`, `Docx2txtLoader`, custom `pandas` Excel loader) and chunked using `RecursiveCharacterTextSplitter`.
3. **Vectorization**: Chunks are embedded and stored in `./chroma_db`.
4. **Querying**: The `/api/query` endpoint retrieves top relevant context chunks and passes them to Groq's LLM with context-bounded prompting.

---

### Getting Started

#### Prerequisites

* Python 3.10+
* Groq API Key

#### Installation

1. **Clone the repository**:
   ```bash
   git clone [https://github.com/tomodjuro/Engineering-Intelligence-Hub-RAG-API-.git](https://github.com/tomodjuro/Engineering-Intelligence-Hub-RAG-API-.git)
   cd Engineering-Intelligence-Hub-RAG-API-
   ```

2. **Set up a virtual environment**:
   * **On Windows**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```
   * **On macOS/Linux**:
     ```bash
     python -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**:
   Configure `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

#### Running the API

Start the FastAPI application with Uvicorn:

```bash
uvicorn main:app --reload
```

The server will be live at `http://127.0.0.1:8000`.  
Interactive API documentation (Swagger UI) is available at `http://127.0.0.1:8000/docs`.

<img width="842" height="338" alt="slika" src="https://github.com/user-attachments/assets/51b6a2f3-89c0-45ee-88c2-c35d8226a902" />
