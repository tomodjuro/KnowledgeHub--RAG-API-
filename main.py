import os
import shutil
import asyncio
import logging
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

from rag_chain import (
    get_vector_store,
    get_rag_chain,
    generate_rag_stream,
    process_and_index_file,
    reindex_all_docs,
    sync_missing_or_modified_docs,
    delete_doc_from_chroma,
    DOCS_DIR
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx", ".doc", ".xlsx", ".xls"}

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("[STARTUP] API server started. Running smart document synchronization...")
    asyncio.create_task(asyncio.to_thread(sync_missing_or_modified_docs))
    yield
    logging.info("[SHUTDOWN] API server shutting down...")

app = FastAPI(
    title="Hub API",
    description="RAG-based Document Management & Query API",
    version="1.0.0",
    lifespan=lifespan
)

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    sources: list

@app.get("/")
def read_root():
    return {"message": "DocuBrain API is running."}

@app.post("/api/v1/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    try:
        rag_chain = get_rag_chain()
        response = rag_chain.invoke({"input": request.question})
        
        sources = []
        if "context" in response:
            for doc in response["context"]:
                source_name = doc.metadata.get("source", "Unknown")
                source_basename = os.path.basename(str(source_name))
                if source_basename not in sources:
                    sources.append(source_basename)

        return QueryResponse(
            answer=response["answer"],
            sources=sources
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing error: {str(e)}")

@app.post("/api/v1/query-stream")
async def query_rag_stream(request: QueryRequest):
    try:
        return StreamingResponse(
            generate_rag_stream(request.question),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Streaming initialization error: {str(e)}")

@app.get("/api/v1/documents")
def get_all_documents():
    """Returns a list of all currently indexed files in ChromaDB."""
    try:
        vector_store = get_vector_store()
        collection_data = vector_store._collection.get(include=["metadatas"])
        metadatas = collection_data.get("metadatas", [])
        
        filenames = set()
        for meta in metadatas:
            if meta:
                src = meta.get("source") or meta.get("file_path") or meta.get("filename")
                if src:
                    filenames.add(os.path.basename(str(src)))
        
        return {
            "documents": sorted(list(filenames)),
            "count": len(filenames)
        }
    except Exception as e:
        logging.error(f"Error fetching document list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/upload", status_code=202)
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # Strip any directory components the client might send (path-traversal guard)
    safe_filename = os.path.basename(file.filename or "")
    if not safe_filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    ext = os.path.splitext(safe_filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)

    file_path = os.path.join(DOCS_DIR, safe_filename)

    # Defense in depth: confirm the resolved path is still inside DOCS_DIR
    if os.path.commonpath([os.path.abspath(file_path), os.path.abspath(DOCS_DIR)]) != os.path.abspath(DOCS_DIR):
        raise HTTPException(status_code=400, detail="Invalid filename.")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(process_and_index_file, file_path)

    return {
        "message": f"File '{safe_filename}' uploaded successfully and queued for indexing.",
        "status": "processing"
    }

class IndexExistingRequest(BaseModel):
    filename: str

@app.post("/api/v1/index-existing", status_code=202)
async def index_existing_document(request: IndexExistingRequest, background_tasks: BackgroundTasks):
    """
    Notify-only endpoint for the folder watcher: the file already lives on disk
    in DOCS_DIR (shared volume), so unlike /api/v1/upload this does NOT rewrite
    it. That rewrite was retriggering the watcher's on_modified handler and
    causing an infinite upload->write->modify->upload loop.
    """
    safe_filename = os.path.basename(request.filename or "")
    if not safe_filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    file_path = os.path.join(DOCS_DIR, safe_filename)

    if os.path.commonpath([os.path.abspath(file_path), os.path.abspath(DOCS_DIR)]) != os.path.abspath(DOCS_DIR):
        raise HTTPException(status_code=400, detail="Invalid filename.")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File '{safe_filename}' not found in docs directory.")

    background_tasks.add_task(process_and_index_file, file_path)

    return {
        "message": f"Indexing triggered for existing file '{safe_filename}'.",
        "status": "processing"
    }

@app.delete("/api/v1/documents/{filename}", status_code=202)
async def delete_document(filename: str, background_tasks: BackgroundTasks):
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(DOCS_DIR, safe_filename)

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            logging.info(f"[API] File deleted from disk: {safe_filename}")
        except Exception as e:
            logging.warning(f"[API WARNING] Error deleting file from disk: {e}")

    background_tasks.add_task(delete_doc_from_chroma, safe_filename)

    return {
        "message": f"Deletion request for '{safe_filename}' received.",
        "status": "processing"
    }

@app.post("/api/v1/reindex", status_code=202)
async def reindex_documents(background_tasks: BackgroundTasks):
    background_tasks.add_task(reindex_all_docs)
    return {
        "message": "Full background re-indexing initiated.",
        "status": "processing"
    }