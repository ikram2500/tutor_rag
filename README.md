# TutorRAG

An AI-powered educational assistant that uses **Retrieval-Augmented Generation (RAG)** to help students learn from their own uploaded documents.

## Features

- **Document Upload** – Teachers upload PDF textbooks/notes; the system extracts and indexes them.
- **AI Q&A Chat** – Students ask questions and get answers grounded in the uploaded content with source citations.
- **Quiz Generation** – Students generate multiple-choice quizzes on any topic from the documents.
- **Quiz History** – Review past quiz attempts with per-question feedback.

## Architecture

```
Streamlit Client  ──HTTP──>  FastAPI Backend  ──>  MongoDB (text, users, history)
                                        ──>  Pinecone (vector embeddings)
                                        ──>  Google GenAI (embeddings)
                                        ──>  Groq LLM (answer generation)
```

## Tech Stack

| Component | Technology |
|---|---|
| Backend | FastAPI (Python) |
| Frontend | Streamlit |
| LLM | Groq (Llama 3.3 70B) |
| Embeddings | Google Gemini Embedding 001 |
| Vector Store | Pinecone |
| Document Store | MongoDB Atlas |
| Auth | HTTP Basic Auth + bcrypt |
| PDF Parsing | LangChain PyPDFLoader |

## Project Structure

```
server/              # FastAPI backend
  main.py            # App entry point, routers
  config/db.py       # MongoDB connection & collections
  auth/              # Signup, login, auth utilities
  docs/              # PDF upload, chunking, vector storage
  chat/              # Q&A chat, quiz generation & grading
client/              # Streamlit frontend
  main.py            # Multi-page UI (landing, login, signup, dashboards)
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r server/requirements.txt

# Configure server/.env with your API keys (MongoDB, Pinecone, Groq, Google)

uvicorn server.main:app --reload --port 8000

# In a separate terminal:
pip install -r client/requirements.txt
streamlit run client/main.py
```

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/signup/student` | No | Register student |
| POST | `/signup/teacher` | No | Register teacher |
| GET | `/login` | Basic | Authenticate user |
| POST | `/upload_docs` | Basic | Upload PDF (Teacher) |
| POST | `/chat` | Basic | Ask question (Student) |
| POST | `/quiz` | Basic | Generate quiz (Student) |
| POST | `/quiz/check` | Basic | Submit quiz answers (Student) |
| GET | `/quiz/history` | Basic | View quiz history (Student) |
