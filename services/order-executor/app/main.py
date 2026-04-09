import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, init_signals_table, get_all_trades, get_signals
from app.executor import execute_trade
from app.consumer import start_consumer_thread
from app.binance_executor import get_testnet_balance
from app.config import HOST, PORT
from prometheus_fastapi_instrumentator import Instrumentator


app = FastAPI(
    title="Order Executor",
    description="Paper trading execution service with Binance Testnet",
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
    print("Order Executor started!")

@app.get("/health")
def health():
    return {"status": "ok", "service": "order-executor"}

@app.post("/execute/{symbol}")
def execute(symbol: str):
    symbol = symbol.replace("-", "/").upper()
    return execute_trade(symbol)

@app.get("/signal/{symbol}")
def get_signal_only(symbol: str):
    """Get ML signal without executing — ML Engine logs the signal"""
    symbol = symbol.replace("-", "/").upper()
    try:
        from app.executor import get_latest_candle, get_ml_signal, get_latest_price
        candle = get_latest_candle(symbol)
        if not candle:
            return {"signal": "UNKNOWN", "confidence": 0, "price": 0}
        signal_data = get_ml_signal(symbol, candle)
        price = get_latest_price(symbol)
        if not signal_data:
            return {"signal": "UNKNOWN", "confidence": 0, "price": price}
        return {
            "signal":     signal_data['signal'],
            "confidence": signal_data['confidence'],
            "model":      signal_data.get('model', 'Unknown'),
            "price":      price
        }
    except Exception as e:
        return {"signal": "ERROR", "confidence": 0, "price": 0, "error": str(e)}
    symbol = symbol.replace("-", "/").upper()
    try:
        from app.executor import get_latest_candle, get_ml_signal, get_latest_price
        candle = get_latest_candle(symbol)
        if not candle:
            return {"signal": "UNKNOWN", "confidence": 0, "price": 0}
        signal_data = get_ml_signal(symbol, candle)
        price = get_latest_price(symbol)
        if not signal_data:
            return {"signal": "UNKNOWN", "confidence": 0, "price": price}
        return {
            "signal":     signal_data['signal'],
            "confidence": signal_data['confidence'],
            "model":      signal_data.get('model', 'Unknown'),
            "price":      price
        }
    except Exception as e:
        return {"signal": "ERROR", "confidence": 0, "price": 0, "error": str(e)}
    symbol = symbol.replace("-", "/").upper()
    try:
        from app.executor import get_latest_candle, get_ml_signal, get_latest_price
        from app.database import save_signal
        candle = get_latest_candle(symbol)
        if not candle:
            return {"signal": "UNKNOWN", "confidence": 0, "price": 0}
        signal_data = get_ml_signal(symbol, candle)
        price = get_latest_price(symbol)
        if not signal_data:
            return {"signal": "UNKNOWN", "confidence": 0, "price": price}
        
        # Save signal to database
        save_signal({
            "symbol":     symbol,
            "signal":     signal_data['signal'],
            "confidence": signal_data['confidence'],
            "model":      signal_data.get('model', 'Unknown'),
            "price":      price,
            "rsi":        candle.get('rsi', 0),
            "source":     "dashboard"
        })
        
        return {
            "signal":     signal_data['signal'],
            "confidence": signal_data['confidence'],
            "model":      signal_data.get('model', 'Unknown'),
            "price":      price
        }
    except Exception as e:
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