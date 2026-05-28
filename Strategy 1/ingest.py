import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

# Define permissions
PERMISSIONS = {
    "Monish_resume.pdf": ["monish", "admin"],
    "LLMs_Enhanced_Presentation.pdf": ["monish", "bob", "admin"]
}

DATA_DIR = "./data"
CHROMA_PATH = "./chroma_db"

def ingest_docs():
    print("Initializing embeddings...")
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
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
            
            # Add metadata for permissions
            allowed_users = PERMISSIONS.get(filename, [])
            for doc in docs:
                # Store individual boolean flags for each user
                for user in allowed_users:
                    doc.metadata[f"access_{user}"] = True
                doc.metadata["source"] = filename
            
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
            chunks = text_splitter.split_documents(docs)
            all_chunks.extend(chunks)
    
    if not all_chunks:
        print("No documents found to ingest.")
        return

    print(f"Storing {len(all_chunks)} chunks in ChromaDB at {CHROMA_PATH}...")
    # Clear existing DB if it exists (optional, let's keep it simple)
    vector_db = Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )
    print("Ingestion complete.")

if __name__ == "__main__":
    ingest_docs()
