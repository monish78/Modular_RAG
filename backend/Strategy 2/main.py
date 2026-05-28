import os
import csv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Modular RAG Strategy 2: Post-Retrieval Filtering")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db_s2")
LLM_MODEL = "qwen2.5:0.5b"
EMBED_MODEL = "nomic-embed-text"
PERMISSIONS_FILE = os.path.join(os.path.dirname(__file__), "permissions.csv")

class QueryRequest(BaseModel):
    user_name: str
    user_prompt: str

# Load permissions
def load_permissions():
    perms = {}
    if os.path.exists(PERMISSIONS_FILE):
        with open(PERMISSIONS_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                filename = row['filename']
                users = [u.strip().lower() for u in row['allowed_users'].split(',')]
                perms[filename] = users
    return perms

print("Initializing components...")
embeddings = OllamaEmbeddings(model=EMBED_MODEL)
vector_db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
llm = ChatOllama(model=LLM_MODEL)

# Define prompt
system_prompt = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer the question. "
    "If you don't know the answer, just say that you don't know. "
    "Use three sentences maximum and keep the answer concise."
    "\n\n"
    "{context}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

@app.post("/query")
async def query_rag(request: QueryRequest):
    user_name = request.user_name.lower()
    
    # Reload permissions on each request for full dynamism
    permissions = load_permissions()
    
    # 1. Retrieve chunks (no filter)
    # Increase k to ensure we find authorized docs even if they aren't top results
    relevant_docs = vector_db.similarity_search(request.user_prompt, k=10)
    
    # 2. Filter authorized chunks
    authorized_docs = []
    for doc in relevant_docs:
        source = doc.metadata.get("source")
        allowed_users = permissions.get(source, [])
        if user_name in allowed_users:
            authorized_docs.append(doc)
    
    # 3. Check if any chunks remain
    if not authorized_docs:
        return {"response": "you cannot access this file", "sources": []}
    
    # 4. Generate response
    qa_chain = create_stuff_documents_chain(llm, prompt)
    response = qa_chain.invoke({"input": request.user_prompt, "context": authorized_docs})
    
    return {
        "response": response,
        "sources": list(set([doc.metadata.get("source") for doc in authorized_docs]))
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting Strategy 2 server on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
