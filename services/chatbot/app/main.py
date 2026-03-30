import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from app.rag import answer_question
from app.embeddings import build_index
from app.mock_data import seed_database
from app.config import HOST, PORT
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="RAG Chatbot",
    description="Sentiment-aware crypto chatbot powered by Gemini and FAISS",
    version="1.0.0"
)
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
    print("Seeding database with mock posts...")
    seed_database()
    print("Building FAISS index...")
    build_index()
    print("Chatbot ready!")

@app.get("/health")
def health():
    return {"status": "ok", "service": "chatbot"}

@app.post("/ask")
def ask(request: QuestionRequest):
    return answer_question(request.question)

@app.get("/rebuild-index")
def rebuild():
    count = build_index()
    return {"message": f"Index rebuilt with {count} posts"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)