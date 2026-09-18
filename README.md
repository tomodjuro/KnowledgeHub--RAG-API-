[![CI Pipeline](https://github.com/tomodjuro/KnowledgeHub--RAG-API-/actions/workflows/ci.yml/badge.svg)](https://github.com/tomodjuro/KnowledgeHub--RAG-API-/actions)

# KnowledgeHub API (DocuBrain RAG)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0+-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B.svg)](https://streamlit.io/)
[![LangChain](https://img.shields.io/badge/LangChain-Modular-121212.svg)](https://www.langchain.com/)
[![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-purple.svg)](https://www.trychroma.com/)
[![Groq](https://img.shields.io/badge/LLM-Groq%20API-orange.svg)](https://groq.com/)

> An asynchronous Retrieval-Augmented Generation (RAG) system with a real-time streaming API, custom Tkinter Control GUI, automated directory watcher, and Streamlit frontend interface built with FastAPI, LangChain, ChromaDB, and Groq LLM.

---

## Overview

Imagine joining a new company where all guidelines, rules, code, and documentation are scattered across hundreds of different files and formats. Instead of spending days hunting down the right information or constantly interrupting colleagues, this project creates a smart technical assistant for the team.

### What the project does

- **Collects & Reads Documents:** Automatically watches and processes internal technical documentation and code.
- **Smart Ingestion & Syncing:** A smart startup hook checks modified or missing files on disk and indexes only what changed.
- **Token-by-Token Streaming:** Delivers real-time AI responses directly into the Streamlit UI as tokens are generated.
- **Centralized GUI Control:** A unified desktop control panel (`gui_control.py`) manages the API, Watcher, and UI services with reliable process termination.
- **Answers Questions with Citations:** Instantly retrieves context chunks and provides clear answers in English or Croatian with exact source citations.

---

## Key Features

- **Real-time AI Response Streaming:** Dedicated `/api/v1/query-stream` endpoint powered by FastAPI `StreamingResponse` and Streamlit `st.write_stream`.
- **Centralized Desktop GUI:** Tkinter-based control panel (`gui_control.py`) for one-click start and stop of all system components.
- **Automated File System Watcher:** `folder_watcher.py` actively monitors `./docs` for new, modified, or deleted files in real time.
- **Smart Startup Syncing:** Automatic `sync_missing_or_modified_docs` lifespan hook prevents duplicate embedding work on startup.
- **Multi-Format Document Ingestion:** Native support for `.pdf`, `.md`, `.txt`, `.docx` files, and `.xlsx` files using Pandas.
- **Asynchronous Processing:** A non-blocking ingestion pipeline using FastAPI `BackgroundTasks`, returning `202 Accepted` immediately.
- **Enterprise-Grade Vector Search:** Embeddings powered by `sentence-transformers/all-MiniLM-L6-v2` with persistent vector storage in ChromaDB.
- **CI/CD Integration:** Automated testing pipeline using GitHub Actions and `pytest`.

---

## Tech Stack

| Component | Technology |
|:---|:---|
| **Framework** | FastAPI (Python 3.10+) |
| **Frontend UI** | Streamlit |
| **Desktop GUI** | Tkinter (`gui_control.py`) |
| **Orchestration** | LangChain (Modular architecture) |
| **Vector Database** | ChromaDB |
| **Embedding Model** | `sentence-transformers/all-MiniLM-L6-v2` (HuggingFace) |
| **LLM Inference** | Groq API (`openai/gpt-oss-120b`) |
| **File Monitoring** | Watchdog (`folder_watcher.py`) |
| **Parsers & Utilities** | `pypdf`, `python-docx`, `pandas`, `openpyxl`, `python-multipart` |

---

## Architecture Overview

1. **Control Panel:** `gui_control.py` launches and manages the FastAPI API, Watchdog service, and Streamlit Chat UI.
2. **Document Ingestion:** New documents added to `./docs` are automatically indexed by `folder_watcher.py` or uploaded via `/api/v1/upload`.
3. **Parsing & Chunking:** Documents are parsed by format-specific loaders such as `TextLoader`, `PyPDFLoader`, `Docx2txtLoader`, and a custom Pandas Excel loader. The content is split into chunks using `RecursiveCharacterTextSplitter`.
4. **Vector Storage:** Embedded chunks and `last_modified` timestamps are persisted inside `./chroma_db`.
5. **Real-time Querying:** A streaming request to `/api/v1/query-stream` fetches context from ChromaDB and streams Groq LLM tokens live back to Streamlit.

---

## Getting Started

### Prerequisites

- Python 3.10+
- Groq API key

### Installation

#### 1. Clone the repository

```bash
git clone [https://github.com/tomodjuro/KnowledgeHub--RAG-API-.git](https://github.com/tomodjuro/KnowledgeHub--RAG-API-.git)
cd KnowledgeHub--RAG-API-
```

#### 2. Set up a virtual environment

##### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\activate
```

##### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure environment variables

Create a `.env` file in the root directory:

```env
GROQ_API_KEY=your_groq_api_key_here
```

---

## Running the Application

### Option 1: Centralized Control GUI

This is the recommended method. Launch the Tkinter control panel to manage all services from a single interface:

```bash
python gui_control.py
```

Click **“Start All”** to launch the API, Watcher, and Streamlit UI simultaneously.

### Option 2: Manual Service Startup

#### FastAPI Backend

```bash
uvicorn main:app --reload
```

- Server: <http://127.0.0.1:8000>
- Swagger UI: <http://127.0.0.1:8000/docs>

#### Streamlit Frontend

```bash
streamlit run app.py
```

Web interface: <http://localhost:8501>

#### Folder Watcher

```bash
python folder_watcher.py
```

---

## Quick Start with Docker (New Machine Setup)

Follow these steps to deploy and run the entire system on a new computer:

### Prerequisites
* **Docker Desktop** installed and running
* **Python 3.10+** (only required to run the lightweight Tkinter GUI)
* **Groq API Key**

---

Step-by-Step Installation:

1. **Clone the Repository**
   ```bash
   git clone [https://github.com/tomodjuro/KnowledgeHub--RAG-API-.git](https://github.com/tomodjuro/KnowledgeHub--RAG-API-.git)
   cd KnowledgeHub--RAG-API-

2. Configure Environment Variables
Create a .env file in the root directory: GROQ_API_KEY=your_groq_api_key_here

3. Launch the Application

    Option A: Via Control Panel (Recommended)
    Run the lightweight desktop control script in terminal: python gui_control_docker.py # or make desktop shortcut to this script
    Click "⚡ Start Stack" to build and spin up all Docker containers (FastAPI, Streamlit UI, and Folder Watcher) in the background.
    
    Option B: Directly via Docker CLI, in terminal type:  docker compose up -d --build
    Accessing Services:

    Streamlit Chat UI: http://localhost:8501

    FastAPI Backend & Docs: http://localhost:8000/docs

---

## API Endpoints

| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/` | Health check endpoint |
| `POST` | `/api/v1/query` | Standard JSON query response |
| `POST` | `/api/v1/query-stream` | Token-by-token streaming AI response |
| `POST` | `/api/v1/upload` | Upload and background-index a document |
| `DELETE` | `/api/v1/documents/{filename}` | Delete a document from disk and ChromaDB |
| `POST` | `/api/v1/reindex` | Trigger full reindexing of `./docs` |