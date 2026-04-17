import uvicorn
import threading
import asyncio
import json
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
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
    grpc_thread = threading.Thread(target=grpc_serve, daemon=False)
    grpc_thread.start()
    print("Market Data Collector started with REST + gRPC + WebSocket servers!")

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

@app.websocket("/ws/price/{symbol}")
async def websocket_price(websocket: WebSocket, symbol: str):
    """WebSocket endpoint for real-time price updates"""
    await websocket.accept()
    symbol_ccxt = symbol.replace("-", "/")
    print(f"[WebSocket] Client connected for {symbol}")
    try:
        while True:
            try:
                # Run blocking call in thread pool to not block event loop
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(
                    None, get_latest_price, symbol_ccxt
                )
                await websocket.send_json(data)
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"[WebSocket] Error: {e}")
                break
            await asyncio.sleep(2)
    finally:
        print(f"[WebSocket] Client disconnected for {symbol}")