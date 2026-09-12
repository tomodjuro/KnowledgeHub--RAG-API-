import os
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

DOCS_DIR = "./docs"
documents = []

print("Učitavam dokumente iz /docs mape...")

if os.path.exists(DOCS_DIR):
    for root, _, files in os.walk(DOCS_DIR):
        for file in files:
            file_path = os.path.join(root, file)
            
            # 1. Tekstualne i Markdown datoteke
            if file.endswith(('.txt', '.md')):
                loader = TextLoader(file_path, encoding='utf-8')
                documents.extend(loader.load())
            
            # 2. PDF datoteke
            elif file.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
                documents.extend(loader.load())
            
            # 3. Word datoteke (.docx)
            elif file.endswith('.docx'):
                loader = Docx2txtLoader(file_path)
                documents.extend(loader.load())

            # 4. Excel datoteke (.xlsx, .xls)
            elif file.endswith(('.xlsx', '.xls')):
                loader = UnstructuredExcelLoader(file_path, mode="elements")
                documents.extend(loader.load())

print(f"Učitano ukupno dokumenata/stranica: {len(documents)}")

if not documents:
    print("Oprez: Niti jedan podržani dokument (.txt, .md, .pdf, .docx, .xlsx) nije pronađen u /docs mapi.")
    exit()

print("Dijelim tekst na cjeline (chunks)...")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = text_splitter.split_documents(documents)

print(f"Ukupno kreirano cjelina (chunks): {len(chunks)}")

print("Inicijaliziram lokalni embedding model...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

print("Spremam vektore u ChromaDB...")
vector_store = Chroma.from_documents(
    documents=chunks, 
    embedding=embeddings, 
    persist_directory="./chroma_db"
)

print("Gotovo! Baza podataka je uspješno izgrađena u './chroma_db'.")