# Modular RAG Project

This project demonstrates two different strategies for document-level access control in a Retrieval-Augmented Generation (RAG) system.

## Project Structure
- `backend/Strategy 1/`: Vector-level filtering (pre-retrieval). Runs on port 8000.
- `backend/Strategy 2/`: Metadata filtering (post-retrieval). Runs on port 8001.
- `frontend/`: React-based chatbot interface. Runs on port 3000.

## How to Run

### 1. Start the Backend
Depending on which strategy you want to use, navigate to its folder and run:
```bash
python main.py
```
*(Note: Make sure you have installed the requirements and Ollama is running)*

### 2. Start the Frontend
Navigate to the `frontend` folder and run:
```bash
npm run dev
```

### 3. Use the Chatbot
1. Open your browser to `http://localhost:3000`.
2. Enter a **Username** in the top right.
3. Select the **Strategy** that matches the running backend.
4. Start chatting!
