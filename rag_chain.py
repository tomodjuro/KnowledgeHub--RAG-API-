import os
import shutil
from dotenv import load_dotenv
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

load_dotenv()

# Postavke putanja
DOCS_DIR = "./docs"
CHROMA_DIR = "./chroma_db"

os.makedirs(DOCS_DIR, exist_ok=True)

def get_embeddings():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def get_rag_chain():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY nije pronađen u .env datoteci!")

    embeddings = get_embeddings()
    vector_store = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
    retriever = vector_store.as_retriever(search_kwargs={"k": 2})

    llm = ChatGroq(
        temperature=0, 
        model_name="openai/gpt-oss-120b",
        groq_api_key=api_key
    )

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
        # Pretvaranje tablice u tekstualni format pogodan za RAG
        text_content = f"Radni list (Sheet): {sheet_name}\n" + df.to_string(index=False)
        doc = Document(
            page_content=text_content,
            metadata={"source": file_path, "sheet": sheet_name}
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

def process_and_index_file(file_path: str):
    """Pozadinska funkcija za indeksiranje pojedinačne datoteke u Chroma bazu."""
    try:
        documents = _get_documents_for_file(file_path)

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = text_splitter.split_documents(documents)

        embeddings = get_embeddings()
        vector_store = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
        
        vector_store.add_documents(chunks)
        print(f"[BACKGROUND TASK] Uspješno indeksirana datoteka ({os.path.splitext(file_path)[1]}): {file_path}")
    except Exception as e:
        print(f"[BACKGROUND TASK ERROR] Greška pri obradi {file_path}: {e}")

def reindex_all_docs():
    """Prolazi kroz cijelu ./docs mapu i indeksira sve podržane dokumente."""
    supported_extensions = {".pdf", ".txt", ".md", ".docx", ".doc", ".xlsx", ".xls"}
    files_processed = 0

    for root, _, files in os.walk(DOCS_DIR):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in supported_extensions:
                file_path = os.path.join(root, file)
                process_and_index_file(file_path)
                files_processed += 1

    print(f"[REINDEX] Reindeksiranje završeno. Obrađeno datoteka: {files_processed}")