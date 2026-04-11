import uvicorn
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, get_recent_posts, get_sentiment_summary
from app.scraper import scrape_and_save_all
from app.grpc_server import serve as grpc_serve
from app.config import HOST, PORT
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(
    title="Sentiment Collector",
    description="Scrapes Reddit posts and performs sentiment analysis",
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

@app.on_event("startup")
def startup():
    init_db()
    import threading
    from app.grpc_server import serve as grpc_serve
    grpc_thread = threading.Thread(target=grpc_serve, daemon=False)
    grpc_thread.start()
    print("Sentiment Collector started with REST + gRPC servers!")

@app.get("/health")
def health():
    return {"status": "ok", "service": "sentiment-collector"}

@app.post("/scrape")
def scrape():
    scrape_and_save_all()
    return {"message": "Scraping completed"}

@app.get("/posts")
def get_posts(asset: str = None, limit: int = 50):
    return {"posts": get_recent_posts(asset=asset, limit=limit)}

@app.get("/summary/{asset}")
def get_summary(asset: str):
    return get_sentiment_summary(asset)

@app.get("/symbols")
def get_symbols():
    return {"symbols": ["BTC", "ETH", "GENERAL"]}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)