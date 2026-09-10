import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

print("Učitavam dokumente iz /docs mape...")
loader = DirectoryLoader('./docs', glob="**/*.md", loader_cls=TextLoader, loader_kwargs={'encoding': 'utf-8'})
documents = loader.load()

print("Dijelim tekst na cjeline (chunks)...")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = text_splitter.split_documents(documents)

print("Inicijaliziram lokalni embedding model...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

print("Spremam vektore u ChromaDB...")
vector_store = Chroma.from_documents(
    documents=chunks, 
    embedding=embeddings, 
    persist_directory="./chroma_db"
)

print("Gotovo! Baza podataka je spremna u './chroma_db'.")