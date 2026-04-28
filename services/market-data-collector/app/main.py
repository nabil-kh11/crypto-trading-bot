import uvicorn
import threading
import asyncio
import json
import time
import psycopg2
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.collector import fetch_ohlcv, get_latest_price
from app.grpc_server import serve as grpc_serve
from app.config import HOST, PORT, SUPPORTED_SYMBOLS
from prometheus_fastapi_instrumentator import Instrumentator

DATABASE_URL = "postgresql://postgres:admin@postgres:5432/cryptobot"

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

def record_prices():
    """Record BTC and ETH prices every 5 minutes to price_history table"""
    while True:
        try:
            btc = get_latest_price("BTC/USDT")
            eth = get_latest_price("ETH/USDT")
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO price_history (symbol, price) VALUES (%s, %s)",
                ("BTC/USDT", btc["price"])
            )
            cursor.execute(
                "INSERT INTO price_history (symbol, price) VALUES (%s, %s)",
                ("ETH/USDT", eth["price"])
            )
            conn.commit()
            cursor.close()
            conn.close()
            print(f"[PriceHistory] BTC={btc['price']} ETH={eth['price']} recorded")
        except Exception as e:
            print(f"[PriceHistory] Error: {e}")
        time.sleep(300)

@app.on_event("startup")
def startup():
    grpc_thread = threading.Thread(target=grpc_serve, daemon=False)
    grpc_thread.start()
    price_thread = threading.Thread(target=record_prices, daemon=True)
    price_thread.start()
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

@app.get("/price-history")
def get_price_history(limit: int = 1000):
    """Get BTC and ETH price history for portfolio chart"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT symbol, price, recorded_at
            FROM price_history
            ORDER BY recorded_at ASC
            LIMIT %s
        """, (limit,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [
            {"symbol": row[0], "price": row[1], "recorded_at": row[2].isoformat()}
            for row in rows
        ]
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