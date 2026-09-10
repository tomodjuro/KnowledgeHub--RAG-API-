import os
import shutil
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from rag_chain import get_rag_chain, process_and_index_file, reindex_all_docs, DOCS_DIR

app = FastAPI(
    title="Engineering Intelligence Hub API",
    version="1.0.0",
    description="Production-ready RAG API s asinkronim indeksiranjem i masovnim reindeksiranjem."
)

rag_chain = get_rag_chain()

class QueryRequest(BaseModel):
    question: str

@app.get("/")
def home():
    return {"status": "RAG API je aktivan", "version": "1.0.0"}

@app.post("/api/query")
def ask_question(request: QueryRequest):
    try:
        response = rag_chain.invoke({"input": request.question})
        sources = [doc.metadata.get("source", "Nepoznato") for doc in response.get("context", [])]
        
        return {
            "answer": response["answer"],
            "sources": list(set(sources))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/upload", status_code=202)
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Sprema prenesenu datoteku (.pdf, .md, .txt, .docx, .xlsx) i pokreće pozadinsko indeksiranje.
    """
    allowed_extensions = {".md", ".txt", ".pdf", ".docx", ".doc", ".xlsx", ".xls"}
    ext = os.path.splitext(file.filename)[1].lower()
    
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail="Podržani su samo .pdf, .md, .txt, .docx i .xlsx formati."
        )

    file_path = os.path.join(DOCS_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(process_and_index_file, file_path)

    return {
        "message": f"Datoteka '{file.filename}' zaprimljena. Indeksiranje se izvodi u pozadini.",
        "filename": file.filename,
        "status": "processing"
    }

@app.post("/api/v1/reindex", status_code=202)
async def reindex_documents(background_tasks: BackgroundTasks):
    """
    Pokreće pozadinsko reindeksiranje svih dokumenata iz ./docs mape.
    """
    background_tasks.add_task(reindex_all_docs)
    return {
        "message": "Pokrenuto je reindeksiranje svih dokumenata u pozadini.",
        "status": "processing"
    }