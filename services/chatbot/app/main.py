import uvicorn
import threading
from fastapi import FastAPI
from pydantic import BaseModel
from app.rag import answer_question
from app.embeddings import build_index
from app.mock_data import seed_database
from app.grpc_server import serve as grpc_serve
from app.config import HOST, PORT
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(
    title="RAG Chatbot",
    description="Sentiment-aware crypto chatbot powered by Groq and FAISS",
    version="1.0.0"
)
Instrumentator().instrument(app).expose(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str

@app.on_event("startup")
def startup():
    seed_database()
    build_index()
    import threading
    from app.grpc_server import serve as grpc_serve
    grpc_thread = threading.Thread(target=grpc_serve, daemon=False)
    grpc_thread.start()
    print("Chatbot started with REST + gRPC servers!")

@app.get("/health")
def health():
    return {"status": "ok", "service": "chatbot"}

@app.post("/ask")
def ask(request: QuestionRequest):
    result = answer_question(request.question)
    return result

@app.get("/rebuild-index")
def rebuild_index():
    build_index()
    return {"message": "FAISS index rebuilt"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)