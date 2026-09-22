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

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[STARTUP] API server started. Running smart document synchronization...")
    asyncio.create_task(asyncio.to_thread(sync_missing_or_modified_docs))
    yield
    print("[SHUTDOWN] API server shutting down...")

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
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)

    file_path = os.path.join(DOCS_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(process_and_index_file, file_path)

    return {
        "message": f"File '{file.filename}' uploaded successfully and queued for indexing.",
        "status": "processing"
    }

@app.delete("/api/v1/documents/{filename}", status_code=202)
async def delete_document(filename: str, background_tasks: BackgroundTasks):
    file_path = os.path.join(DOCS_DIR, filename)
    
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"[API] File deleted from disk: {filename}")
        except Exception as e:
            print(f"[API WARNING] Error deleting file from disk: {e}")

    background_tasks.add_task(delete_doc_from_chroma, filename)

    return {
        "message": f"Deletion request for '{filename}' received.",
        "status": "processing"
    }

@app.post("/api/v1/reindex", status_code=202)
async def reindex_documents(background_tasks: BackgroundTasks):
    background_tasks.add_task(reindex_all_docs)
    return {
        "message": "Full background re-indexing initiated.",
        "status": "processing"
    }