import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db_s2")
EMBED_MODEL = "nomic-embed-text"

def ingest_docs():
    print("Initializing embeddings...")
    embeddings = OllamaEmbeddings(model=EMBED_MODEL)
    
    all_chunks = []
    
    if not os.path.exists(DATA_DIR):
        print(f"Error: Data directory {DATA_DIR} not found.")
        return

    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".pdf"):
            file_path = os.path.join(DATA_DIR, filename)
            print(f"Processing {filename}...")
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            
            # Add ONLY source filename to metadata
            for doc in docs:
                doc.metadata["source"] = filename
            
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
            chunks = text_splitter.split_documents(docs)
            all_chunks.extend(chunks)
    
    if not all_chunks:
        print("No documents found to ingest.")
        return

    print(f"Storing {len(all_chunks)} chunks in ChromaDB at {CHROMA_PATH}...")
    vector_db = Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )
    print("Ingestion complete for Strategy 2.")

if __name__ == "__main__":
    ingest_docs()
