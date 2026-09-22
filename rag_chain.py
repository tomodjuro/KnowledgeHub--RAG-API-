import os
import sys
import shutil
import logging
from dotenv import load_dotenv
from typing import Generator
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import (
    TextLoader, 
    PyPDFLoader, 
    Docx2txtLoader, 
    UnstructuredExcelLoader
)
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Dinamičko određivanje korijenske mape (podržava i .py i PyInstaller .exe okruženje)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DOCS_DIR = os.path.join(BASE_DIR, "docs")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

load_dotenv(os.path.join(BASE_DIR, ".env"))
os.makedirs(DOCS_DIR, exist_ok=True)

def get_embeddings():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def get_vector_store():
    """Helper za dohvat Chroma baze."""
    embeddings = get_embeddings()
    return Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)

def get_llm():
    """Helper za inicijalizaciju LLM modela."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY nije pronađen u .env datoteci!")
    
    return ChatGroq(
        temperature=0, 
        model_name="openai/gpt-oss-120b",
        groq_api_key=api_key
    )

def get_rag_chain():
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"k": 2})
    llm = get_llm()

    system_prompt = (
        "Ti si stručni tehnički asistent. Odgovaraj na pitanja isključivo na temelju priloženog konteksta. "
        "Ako u kontekstu nema odgovora, jasno reci da ne znaš.\n\n"
        "Kontekst:\n{context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, question_answer_chain)

def _load_excel_file(file_path: str):
    """Pomoćna funkcija za čitanje Excel datoteka pomoću pandas biblioteke."""
    import pandas as pd
    excel_data = pd.read_excel(file_path, sheet_name=None)
    documents = []
    
    for sheet_name, df in excel_data.items():
        text_content = f"Radni list (Sheet): {sheet_name}\n" + df.to_string(index=False)
        doc = Document(
            page_content=text_content,
            metadata={"source": os.path.basename(file_path), "sheet": sheet_name}
        )
        documents.append(doc)
    return documents

def _get_documents_for_file(file_path: str):
    """Odabire odgovarajući loader i vraća listu dokumenata."""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
        return loader.load()
    elif ext in [".txt", ".md"]:
        loader = TextLoader(file_path, encoding='utf-8')
        return loader.load()
    elif ext in [".docx", ".doc"]:
        loader = Docx2txtLoader(file_path)
        return loader.load()
    elif ext in [".xlsx", ".xls"]:
        return _load_excel_file(file_path)
    else:
        raise ValueError(f"Nepodržani format datoteke: {ext}")

def delete_doc_from_chroma(filename: str) -> int:
    """Pronalazi i briše sve vektorske fragmente povezane s datotekom iz ChromaDB baze."""
    try:
        vector_store = get_vector_store()
        
        # 1. Dohvaćanje svih dokumenata za provjeru imena datoteke neovisno o prefiksima putanje
        existing_docs = vector_store._collection.get(include=["metadatas"])
        ids_to_delete = []
        
        if existing_docs and "metadatas" in existing_docs:
            for doc_id, meta in zip(existing_docs["ids"], existing_docs["metadatas"]):
                if meta:
                    src = meta.get("source") or meta.get("file_path") or meta.get("filename") or meta.get("file_name")
                    if src and os.path.basename(str(src)) == filename:
                        ids_to_delete.append(doc_id)

        if ids_to_delete:
            vector_store._collection.delete(ids=ids_to_delete)
            print(f"[CHROMA] Uspješno obrisano {len(ids_to_delete)} fragmenta za datoteku: {filename}")
            return len(ids_to_delete)
        
        print(f"[CHROMA] Nisu pronađeni vektori za datoteku: {filename}")
        return 0
    except Exception as e:
        print(f"[CHROMA ERROR] Greška pri brisanju dokumenta {filename}: {e}")
        return 0

def process_and_index_file(file_path: str):
    """Pozadinska funkcija za indeksiranje pojedinačne datoteke u Chroma bazu sa spremanjem mtime."""
    filename = os.path.basename(file_path)
    try:
        # 1. Prvo brišemo postojeće fragmente iz baze
        delete_doc_from_chroma(filename)

        # 2. Učitavamo datoteku i dodajemo svježe metapodatke
        documents = _get_documents_for_file(file_path)
        file_mtime = os.path.getmtime(file_path)

        for doc in documents:
            doc.metadata["source"] = filename
            doc.metadata["last_modified"] = file_mtime

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = text_splitter.split_documents(documents)

        # 3. Indeksiramo nove fragmente
        vector_store = get_vector_store()
        vector_store.add_documents(chunks)
        print(f"[BACKGROUND TASK] Uspješno indeksirana datoteka ({os.path.splitext(file_path)[1]}): {filename}")
    except Exception as e:
        print(f"[BACKGROUND TASK ERROR] Greška pri obradi {filename}: {e}")

def reindex_all_docs():
    """Prolazi kroz cijelu ./docs mapu i indeksira sve podržane dokumente."""
    supported_extensions = {".pdf", ".txt", ".md", ".docx", ".doc", ".xlsx", ".xls"}
    files_processed = 0

    for root, _, files in os.walk(DOCS_DIR):
        for file in files:
            if file.startswith("~$") or file.startswith("."):
                continue
            ext = os.path.splitext(file)[1].lower()
            if ext in supported_extensions:
                file_path = os.path.join(root, file)
                process_and_index_file(file_path)
                files_processed += 1

    print(f"[REINDEX] Reindeksiranje završeno. Obrađeno datoteka: {files_processed}")

def sync_missing_or_modified_docs():
    """Prolazi kroz docs/ i indeksira nove/izmijenjene, a briše obrisane datoteke iz baze."""
    supported_extensions = {".pdf", ".txt", ".md", ".docx", ".doc", ".xlsx", ".xls"}
    vector_store = get_vector_store()
    
    indexed_files = {}
    db_filenames = set()
    
    try:
        existing_docs = vector_store._collection.get(include=["metadatas"])
        if existing_docs and "metadatas" in existing_docs:
            for meta in existing_docs["metadatas"]:
                if meta:
                    src = meta.get("source") or meta.get("file_path") or meta.get("filename")
                    if src:
                        fname = os.path.basename(str(src))
                        db_filenames.add(fname)
                        mtime = meta.get("last_modified", 0)
                        indexed_files[fname] = max(indexed_files.get(fname, 0), mtime)
    except Exception as e:
        print(f"[SYNC WARNING] Nije moguće dohvatiti postojeće metapodatke iz baze: {e}")

    # 1. Provjera novih i izmijenjenih datoteka na disku
    disk_files = set()
    files_to_update = []
    
    for root, _, files in os.walk(DOCS_DIR):
        for file in files:
            if file.startswith("~$") or file.startswith("."):
                continue
            
            ext = os.path.splitext(file)[1].lower()
            if ext in supported_extensions:
                disk_files.add(file)
                file_path = os.path.join(root, file)
                disk_mtime = os.path.getmtime(file_path)
                
                if file not in indexed_files or disk_mtime > indexed_files[file]:
                    files_to_update.append(file_path)

    # 2. Uklanjanje datoteka koje više ne postoje na disku
    deleted_files = db_filenames - disk_files
    for deleted_file in deleted_files:
        print(f"[SYNC] Detektirano brisanje na disku, uklanjam iz baze: {deleted_file}")
        delete_doc_from_chroma(deleted_file)

    # 3. Indeksiranje novih/izmijenjenih
    if files_to_update:
        print(f"[SYNC] Pronađeno {len(files_to_update)} novih/izmijenjenih datoteka. Pokrećem indeksiranje...")
        for file_path in files_to_update:
            process_and_index_file(file_path)
        print("[SYNC] Sinkronizacija uspješno završena.")
    else:
        print("[SYNC] Sve datoteke u docs/ su ažurne.")

def generate_rag_stream(question: str) -> Generator[str, None, None]:
    """Generira tok tokena u realnom vremenu (streaming) iz LLM-a."""
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    docs = retriever.invoke(question)

    if not docs:
        yield "Nažalost, u bazi znanja nisam pronašao nikakve relevantne dokumente za vaše pitanje."
        return

    context_blocks = []
    sources = set()

    for doc in docs:
        meta = doc.metadata or {}
        source_path = meta.get("source") or meta.get("file_path") or meta.get("filename") or "Nepoznato"
        source_name = os.path.basename(str(source_path))
        
        if source_name != "Nepoznato":
            sources.add(source_name)

        context_blocks.append(f"--- DOKUMENT: {source_name} ---\n{doc.page_content}")

    full_context = "\n\n".join(context_blocks)

    prompt = (
        "Ti si stručni tehnički asistent za internu dokumentaciju. "
        "Tvoj zadatak je dati detaljan, točan i strukturiran odgovor na temelju priloženih dokumenata.\n\n"
        "UPUTE:\n"
        "- Odgovaraj ISKLJUČIVO na temelju priloženog konteksta.\n"
        "- Ako u kontekstu nema dovoljno informacija za potpun odgovor, jasno reci što nedostaje.\n"
        "- Ako kontekst sadrži relevantne detalje, objasni ih jasno i temeljito.\n\n"
        f"KONTEKST:\n{full_context}\n\n"
        f"PITANJE: {question}\n\n"
        "ODGOVOR:"
    )

    llm = get_llm()
    for chunk in llm.stream(prompt):
        content = getattr(chunk, "content", str(chunk))
        yield content

    if sources:
        sources_formatted = "\n".join([f"* `{src}`" for src in sorted(sources)])
        yield f"\n\n**Izvori:**\n{sources_formatted}"