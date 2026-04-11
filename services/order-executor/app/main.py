import uvicorn
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, init_signals_table, get_all_trades, get_signals
from app.executor import execute_trade
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

@app.on_event("startup")
def startup():
    init_db()
    init_signals_table()
    start_consumer_thread()
    import threading
    from app.grpc_server import serve as grpc_serve
    grpc_thread = threading.Thread(target=grpc_serve, daemon=False)
    grpc_thread.start()
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

        # Build features from candle
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

        print(f"[Signal Debug] Features count: {len(features)}, candle keys: {list(candle.keys())}")

        if len(features) < 10:
            return {"signal": "UNKNOWN", "confidence": 0, "price": price}

        # Call ML engine via gRPC
        channel = grpc.insecure_channel('ml-decision-engine:50052')
        stub = ml_engine_pb2_grpc.MLEngineServiceStub(channel)
        request = ml_engine_pb2.PredictRequest(
            symbol=symbol,
            features=features,
            publish=False
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
    }

@app.get("/trades")
def get_trades(symbol: str = None, limit: int = 50):
    return {"trades": get_all_trades(symbol=symbol, limit=limit)}

@app.get("/symbols")
def symbols():
    return {"symbols": ["BTC/USDT", "ETH/USDT"]}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)