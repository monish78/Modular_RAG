import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langfuse import Langfuse
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db_s2")
EMBED_MODEL = "nomic-embed-text"

# Initialize Langfuse
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST")
)

def ingest_docs():
    trace = langfuse.trace(name="ingestion_strategy_2")
    
    print("Initializing embeddings...")
    embeddings = OllamaEmbeddings(model=EMBED_MODEL)
    
    all_chunks = []
    
    if not os.path.exists(DATA_DIR):
        print(f"Error: Data directory {DATA_DIR} not found.")
        trace.update(status_message="Data directory not found", level="ERROR")
        return

    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".pdf"):
            span = trace.span(name=f"process_{filename}")
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
            span.end(metadata={"chunks": len(chunks)})
    
    if not all_chunks:
        print("No documents found to ingest.")
        trace.update(status_message="No docs found", level="WARNING")
        return

    print(f"Storing {len(all_chunks)} chunks in ChromaDB at {CHROMA_PATH}...")
    vector_db = Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )
    
    trace.update(metadata={"total_chunks": len(all_chunks)}, status_message="Success")
    print("Ingestion complete for Strategy 2.")

if __name__ == "__main__":
    ingest_docs()
