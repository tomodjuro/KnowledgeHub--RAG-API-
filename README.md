# Engineering Intelligence Hub (RAG API)

> A production-ready, asynchronous Retrieval-Augmented Generation (RAG) API built with FastAPI, LangChain, ChromaDB, and Groq LLM for intelligent document querying across enterprise file formats.

## Key Features

- **Multi-Format Document Ingestion**: Native support for `.md`, `.txt`, `.pdf`, `.docx` (Word), and `.xlsx` (Excel).
- **Asynchronous Processing**: Non-blocking ingestion pipeline using FastAPI `BackgroundTasks` (returns `202 Accepted` immediately).
- **Incremental Reindexing**: Batch processing via `/api/v1/reindex` for directory-wide document syncing.
- **Enterprise-Grade Vector Search**: Embeddings powered by `sentence-transformers/all-MiniLM-L6-v2` with persistent vector storage in `ChromaDB`.
- **Fast LLM Inference**: Integration with Groq API (`openai/gpt-oss-120b`) for rapid context-aware responses.

---

## Tech Stack

- **Framework**: FastAPI (Python 3)
- **Orchestration**: LangChain (Modular architecture)
- **Vector Database**: ChromaDB
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (HuggingFace)
- **LLM**: Groq API (`openai/gpt-oss-120b`)
- **Parsers & Utilities**: `pypdf`, `python-docx`, `pandas`, `openpyxl`, `python-multipart`

---

## Architecture Overview

1. **Upload / Reindex**: Incoming documents are saved to `./docs` and dispatched to background workers.
2. **Parsing & Chunking**: Documents are parsed by format-specific loaders (`TextLoader`, `PyPDFLoader`, `Docx2txtLoader`, custom `pandas` Excel loader) and chunked using `RecursiveCharacterTextSplitter`.
3. **Vectorization**: Chunks are embedded and stored in `./chroma_db`.
4. **Querying**: The `/api/query` endpoint retrieves top relevant context chunks and passes them to Groq's LLM with context-bounded prompting.

---

## Getting Started

### Prerequisites

- Python 3.10+
- Groq API Key

### Installation

1. **Clone the repository**:
   ```bash
   git clone [https://github.com/YOUR_USERNAME/engineering-intelligence-hub.git](https://github.com/YOUR_USERNAME/engineering-intelligence-hub.git)
   cd engineering-intelligence-hub
   
2. **Set up a virtual environment**:
python -m venv venv
 **On Windows**:
.\venv\Scripts\activate
 **On macOS/Linux**:
source venv/bin/activate

3. **Install dependencies**
pip install -r requirements.txt

4. Environment Configuration:
Configure .env file in the root directory:
GROQ_API_KEY= your_groq_api_key_here

5. **Running the API**

Start the FastAPI application with Uvicorn:

uvicorn main:app --reload

The server will be live at http://127.0.0.1:8000.
Interactive API documentation (Swagger UI) is available at http://127.0.0.1:8000/docs.

<img width="842" height="338" alt="slika" src="https://github.com/user-attachments/assets/51b6a2f3-89c0-45ee-88c2-c35d8226a902" />
