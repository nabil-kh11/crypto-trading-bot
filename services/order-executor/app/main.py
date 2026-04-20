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

@app.post("/execute/{symbol}")
def execute(symbol: str):
    symbol = symbol.replace("-", "/").upper()
    return execute_trade(symbol)

@app.get("/signal/{symbol}")
def get_signal_only(symbol: str):
    symbol = symbol.replace("-", "/").upper()
    try:
        import grpc
        from app import ml_engine_pb2, ml_engine_pb2_grpc
        from app.executor import get_latest_candle, get_latest_price

        candle = get_latest_candle(symbol)
        price = get_latest_price(symbol)

        if not candle:
            return {"signal": "UNKNOWN", "confidence": 0, "price": price}

        FEATURE_COLS = [
            'ma20', 'ma50', 'ma200', 'rsi', 'returns', 'vol_20',
            'macd', 'macd_signal', 'macd_diff',
            'bb_high', 'bb_low', 'bb_mid', 'bb_width', 'bb_pct',
            'atr', 'stoch_rsi', 'stoch_rsi_k', 'stoch_rsi_d',
            'volume_ratio', 'dist_ma200', 'dist_ma50',
            'hour', 'day_of_week',
            'close_lag_1', 'returns_lag_1',
            'close_lag_2', 'returns_lag_2',
            'close_lag_3', 'returns_lag_3',
            'close_lag_6', 'returns_lag_6',
            'close_lag_12', 'returns_lag_12',
            'close_lag_24', 'returns_lag_24'
        ]

        features = {}
        for col in FEATURE_COLS:
            if col in candle:
                features[col] = float(candle[col])

        if len(features) < 10:
            return {"signal": "UNKNOWN", "confidence": 0, "price": price}

        channel = grpc.insecure_channel('ml-decision-engine:50052')
        stub = ml_engine_pb2_grpc.MLEngineServiceStub(channel)
        request = ml_engine_pb2.PredictRequest(
            symbol=symbol, features=features, publish=False
        )
        response = stub.Predict(request, timeout=10)

        return {
            "signal": response.signal,
            "confidence": response.confidence,
            "model": response.model,
            "price": price
        }
    except Exception as e:
        print(f"[Signal] Error: {e}")
        return {"signal": "ERROR", "confidence": 0, "price": 0, "error": str(e)}

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