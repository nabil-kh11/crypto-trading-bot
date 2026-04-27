import uvicorn
import threading
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, init_signals_table, get_all_trades, get_signals, get_trades_count
from app.executor import execute_trade, get_active_strategy_name, set_strategy, STRATEGIES
from app.consumer import start_consumer_thread
from app.binance_executor import get_testnet_balance
from app.grpc_server import serve as grpc_serve
from app.config import HOST, PORT
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(
    title="Order Executor",
    description="Trading execution service with Binance Testnet",
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

# Price cache — updated every 60 seconds in background
_price_cache = {"BTC_PRICE": 0.0, "ETH_PRICE": 0.0}

def update_price_cache():
    while True:
        try:
            import grpc
            from app import market_data_pb2, market_data_pb2_grpc
            channel = grpc.insecure_channel('market-data-collector:50051')
            stub = market_data_pb2_grpc.MarketDataServiceStub(channel)
            btc = stub.GetPrice(market_data_pb2.PriceRequest(symbol='BTC-USDT'), timeout=10)
            eth = stub.GetPrice(market_data_pb2.PriceRequest(symbol='ETH-USDT'), timeout=10)
            _price_cache["BTC_PRICE"] = float(btc.price)
            _price_cache["ETH_PRICE"] = float(eth.price)
            print(f"[PriceCache] BTC={btc.price:.2f} ETH={eth.price:.2f}")
        except Exception as e:
            print(f"[PriceCache] Error: {e}")
        time.sleep(60)

@app.on_event("startup")
def startup():
    init_db()
    init_signals_table()
    start_consumer_thread()

    grpc_thread = threading.Thread(target=grpc_serve, daemon=False)
    grpc_thread.start()

    price_thread = threading.Thread(target=update_price_cache, daemon=True)
    price_thread.start()

    print("Order Executor started with REST + gRPC servers!")

@app.get("/health")
def health():
    return {"status": "ok", "service": "order-executor"}

@app.get("/signals")
def get_signals_history(symbol: str = None, limit: int = 100):
    return {"signals": get_signals(symbol=symbol, limit=limit)}

@app.get("/balance")
def get_balance():
    return {
        "source": "Binance Testnet",
        "USDT": get_testnet_balance('USDT'),
        "BTC":  get_testnet_balance('BTC'),
        "ETH":  get_testnet_balance('ETH'),
        "BTC_PRICE": _price_cache["BTC_PRICE"],
        "ETH_PRICE": _price_cache["ETH_PRICE"],
    }

@app.get("/trades")
def get_trades(symbol: str = None, limit: int = 10, offset: int = 0):
    return {
        "trades": get_all_trades(symbol=symbol, limit=limit, offset=offset),
        "total": get_trades_count(symbol=symbol)
    }

@app.get("/symbols")
def symbols():
    return {"symbols": ["BTC/USDT", "ETH/USDT"]}

@app.get("/strategy")
def get_strategy():
    name = get_active_strategy_name()
    return {
        "active": name,
        "strategy": STRATEGIES[name],
        "available": list(STRATEGIES.keys())
    }

@app.post("/strategy/{name}")
def change_strategy(name: str):
    if set_strategy(name):
        return {"message": f"Strategy changed to {name}", "active": name}
    raise HTTPException(status_code=400, detail=f"Unknown strategy: {name}")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)