import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.collector import fetch_ohlcv, get_latest_price
from app.config import SYMBOLS, PORT, HOST
from prometheus_fastapi_instrumentator import Instrumentator
app = FastAPI(
    title="Market Data Collector",
    description="Fetches real-time and historical OHLCV data from Binance",
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

@app.get("/health")
def health():
    return {"status": "ok", "service": "market-data-collector"}

@app.get("/ohlcv/{symbol}")
def get_ohlcv(symbol: str, limit: int = 100):
    symbol = symbol.replace("-", "/").upper()
    if symbol not in SYMBOLS:
        raise HTTPException(status_code=400, detail=f"Symbol {symbol} not supported")
    df = fetch_ohlcv(symbol, limit=limit)
    return df.to_dict(orient="records")

@app.get("/price/{symbol}")
def get_price(symbol: str):
    symbol = symbol.replace("-", "/").upper()
    if symbol not in SYMBOLS:
        raise HTTPException(status_code=400, detail=f"Symbol {symbol} not supported")
    return get_latest_price(symbol)

@app.get("/symbols")
def get_symbols():
    return {"symbols": SYMBOLS}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)