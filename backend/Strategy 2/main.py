import os
import csv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
import re

from fastapi.middleware.cors import CORSMiddleware
from langfuse.callback import CallbackHandler
from dotenv import load_dotenv

load_dotenv()

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

# Initialize Langfuse Callback Handler
langfuse_handler = CallbackHandler(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST")
)

def apply_guardrails(prompt: str):
    """
    Advanced Guardrail Suite:
    1. Prompt Injection Protection
    2. PII Detection (Emails)
    3. Malicious Keyword Detection
    """
    # 1. Prompt Injection Patterns
    injection_patterns = [
        r"ignore (all )?previous instructions",
        r"system override",
        r"new role:",
        r"you are now (an )?expert in",
        r"instead of your instructions"
    ]
    for pattern in injection_patterns:
        if re.search(pattern, prompt, re.IGNORECASE):
            return False, "Guardrail Exception: Potential Prompt Injection detected."

    # 2. PII Detection (Email)
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    if re.search(email_pattern, prompt):
        return False, "Guardrail Exception: PII (Email address) detected in prompt. Please remove sensitive information."

    # 3. Prohibited Keywords
    prohibited_keywords = ["delete", "drop table", "system bypass", "unauthorized access"]
    for keyword in prohibited_keywords:
        if keyword in prompt.lower():
            return False, f"Guardrail Exception: Prohibited term '{keyword}' detected."
            
    return True, ""

def sanitize_output(content: str):
    """Simple output guardrail to prevent leaking sensitive info."""
    internal_secrets = ["CONFIDENTIAL_PROJECT_X", "INTERNAL_API_KEY_123"]
    sanitized = content
    for secret in internal_secrets:
        sanitized = sanitized.replace(secret, "[REDACTED]")
    return sanitized

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
    
    # 0. Apply Guardrails
    is_safe, message = apply_guardrails(request.user_prompt)
    if not is_safe:
        # Trace the rejection in Langfuse
        langfuse_handler.langfuse.generation(
            name="guardrail_rejection",
            input=request.user_prompt,
            output=message,
            metadata={"user": user_name}
        )
        return {"response": message, "sources": []}

    # Reload permissions on each request for full dynamism
    permissions = load_permissions()
    
    # 1. Retrieve chunks (no filter)
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
    
    # 4. Generate response with Langfuse tracing
    qa_chain = create_stuff_documents_chain(llm, prompt)
    raw_response = qa_chain.invoke(
        {"input": request.user_prompt, "context": authorized_docs},
        config={"callbacks": [langfuse_handler]}
    )
    
    # Apply Output Guardrail
    response = sanitize_output(raw_response)
    
    return {
        "response": response,
        "sources": list(set([doc.metadata.get("source") for doc in authorized_docs]))
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting Strategy 2 server on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
