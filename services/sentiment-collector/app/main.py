import uvicorn
from fastapi import FastAPI
from app.database import init_db, get_recent_posts, get_sentiment_summary
from app.scraper import scrape_and_save_all
from app.config import HOST, PORT

app = FastAPI(
    title="Sentiment Collector",
    description="Scrapes Reddit posts and performs sentiment analysis",
    version="1.0.0"
)

@app.on_event("startup")
def startup():
    init_db()
    print("Sentiment Collector started!")

@app.get("/health")
def health():
    return {"status": "ok", "service": "sentiment-collector"}

@app.post("/scrape")
def trigger_scrape():
    total = scrape_and_save_all()
    return {"message": f"Scraped {total} posts successfully"}

@app.get("/posts")
def get_posts(asset: str = None, limit: int = 100):
    posts = get_recent_posts(asset=asset, limit=limit)
    return {"total": len(posts), "posts": posts}

@app.get("/summary/{asset}")
def get_summary(asset: str):
    summary = get_sentiment_summary(asset.upper())
    if not summary:
        return {"message": f"No data found for {asset}"}
    return summary

@app.get("/symbols")
def get_symbols():
    return {"assets": ["BTC", "ETH", "GENERAL"]}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)