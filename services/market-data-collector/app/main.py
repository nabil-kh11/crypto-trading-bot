import uvicorn
import threading
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.collector import fetch_ohlcv, get_latest_price
from app.grpc_server import serve as grpc_serve
from app.config import HOST, PORT, SUPPORTED_SYMBOLS
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(
    title="Market Data Collector",
    description="Fetches real-time OHLCV data from Binance",
    version="2.0.0"
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
    import threading
    from app.grpc_server import serve as grpc_serve
    grpc_thread = threading.Thread(target=grpc_serve, daemon=False)
    grpc_thread.start()
    print("Market Data Collector started with REST + gRPC servers!")

@app.get("/health")
def health():
    return {"status": "ok", "service": "market-data-collector"}

@app.get("/symbols")
def get_symbols():
    return {"symbols": SUPPORTED_SYMBOLS}

@app.get("/price/{symbol}")
def get_price(symbol: str):
    symbol_ccxt = symbol.replace("-", "/")
    try:
        return get_latest_price(symbol_ccxt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ohlcv/{symbol}")
def get_ohlcv(symbol: str, limit: int = 100):
    symbol_ccxt = symbol.replace("-", "/")
    try:
        df = fetch_ohlcv(symbol_ccxt, limit=limit)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)