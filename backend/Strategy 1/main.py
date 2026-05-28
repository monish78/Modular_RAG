import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Modular RAG with Access Control")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CHROMA_PATH = "./chroma_db"
LLM_MODEL = "qwen2.5:0.5b" 
EMBED_MODEL = "nomic-embed-text"

class QueryRequest(BaseModel):
    user_name: str
    user_prompt: str

print("Initializing embeddings and vector DB...")
embeddings = OllamaEmbeddings(model=EMBED_MODEL)
vector_db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
llm = ChatOllama(model=LLM_MODEL)

# Define prompt
system_prompt = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer the question. "
    "If no context is provided, respond with 'no info available to you'. "
    "If you don't know the answer, just say that you don't know. "
    "Use three sentences maximum and keep the answer concise."
    "\n\n"
    "{context}"
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

@app.post("/query")
async def query_rag(request: QueryRequest):
    user_name = request.user_name.lower()
    
    # Configure retriever with metadata filter
    # Filter for access_{user_name} == True
    filter_key = f"access_{user_name}"
    search_kwargs = {
        "filter": {filter_key: True},
        "k": 3
    }
    
    retriever = vector_db.as_retriever(search_kwargs=search_kwargs)
    
    # Get relevant docs first to check if any are available
    try:
        relevant_docs = retriever.invoke(request.user_prompt)
    except Exception as e:
        # If the filter key doesn't exist in any doc, Chroma might error or return nothing
        # We handle it as no access
        print(f"Retriever error: {e}")
        relevant_docs = []
    
    if not relevant_docs:
        return {"response": "no info available to you", "sources": []}
    
    print(f"Retrieved {len(relevant_docs)} chunks for {user_name}.")
    for i, doc in enumerate(relevant_docs):
        print(f"--- Chunk {i} ({doc.metadata.get('source')}) ---")
        print(doc.page_content[:200] + "...")
    
    # Create chains
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    
    response = rag_chain.invoke({"input": request.user_prompt})
    
    return {
        "response": response["answer"],
        "sources": list(set([doc.metadata.get("source") for doc in response["context"]]))
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting FastAPI server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
