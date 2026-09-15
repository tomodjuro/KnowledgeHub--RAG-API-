import os
import shutil
import asyncio
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

from rag_chain import (
    get_rag_chain,
    generate_rag_stream,
    process_and_index_file,
    reindex_all_docs,
    sync_missing_or_modified_docs,
    delete_doc_from_chroma,
    DOCS_DIR
)


# --- STARTUP HOOK ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Kôd koji se izvršava pri POKRETANJU API-ja
    print("[STARTUP] API poslužitelj pokrenut. Pokrećem pametnu provjeru dokumenata...")
    asyncio.create_task(asyncio.to_thread(sync_missing_or_modified_docs))
    
    yield  # Ovdje API radi i prima zahtjeve
    
    # Kôd koji se izvršava pri GAŠENJU API-ja (ako zatreba)
    print("[SHUTDOWN] API poslužitelj se gasi...")


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

# --- STANDARDNI QUERY (JSON RESPONSE) ---
@app.post("/api/v1/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    try:
        rag_chain = get_rag_chain()
        response = rag_chain.invoke({"input": request.question})
        
        sources = []
        if "context" in response:
            for doc in response["context"]:
                source_name = doc.metadata.get("source", "Nepoznato")
                if source_name not in sources:
                    sources.append(source_name)

        return QueryResponse(
            answer=response["answer"],
            sources=sources
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Greška pri obradi upita: {str(e)}")

# --- STREAMING QUERY (TOKEN-BY-TOKEN RESPONSE) ---
@app.post("/api/v1/query-stream")
async def query_rag_stream(request: QueryRequest):
    try:
        return StreamingResponse(
            generate_rag_stream(request.question),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Greška pri pokretanju streamanja: {str(e)}")

# --- MANAGEMENT ENDPOINTS ---
@app.post("/api/v1/upload", status_code=202)
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)

    file_path = os.path.join(DOCS_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(process_and_index_file, file_path)

    return {
        "message": f"Datoteka '{file.filename}' je uspješno učitana i spremljena za indeksiranje.",
        "status": "processing"
    }

@app.delete("/api/v1/documents/{filename}", status_code=202)
async def delete_document(filename: str, background_tasks: BackgroundTasks):
    file_path = os.path.join(DOCS_DIR, filename)
    
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"[API] Datoteka obrisana s diska: {filename}")
        except Exception as e:
            print(f"[API WARNING] Greška pri brisanju s diska: {e}")

    background_tasks.add_task(delete_doc_from_chroma, filename)

    return {
        "message": f"Zahtjev za brisanje datoteke '{filename}' zaprimljen.",
        "status": "processing"
    }

@app.post("/api/v1/reindex", status_code=202)
async def reindex_documents(background_tasks: BackgroundTasks):
    background_tasks.add_task(reindex_all_docs)
    return {
        "message": "Pokrenuto potpuno reindeksiranje svih dokumenata u pozadini.",
        "status": "processing"
    }