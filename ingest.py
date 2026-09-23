"""
Standalone CLI script to (re)build the ChromaDB index from the docs folder.

This used to duplicate the loader/chunking logic from rag_chain.py, but with
its own hardcoded relative paths ("./docs", "./chroma_db"). If you ran it
from a different working directory than main.py, it silently built a SECOND,
disconnected Chroma database, so newly ingested files never showed up in the
running API/Streamlit app.

It's now a thin wrapper around rag_chain.py, so there's a single source of
truth for paths (BASE_DIR/docs, BASE_DIR/chroma_db) and indexing logic.
Run it with: python ingest.py
"""
import logging
from rag_chain import reindex_all_docs, DOCS_DIR, CHROMA_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

if __name__ == "__main__":
    logging.info(f"Building/rebuilding index from: {DOCS_DIR}")
    logging.info(f"Chroma persist directory: {CHROMA_DIR}")
    reindex_all_docs()
    logging.info("Gotovo! Indeksiranje završeno.")
