import uvicorn
import datetime
import threading
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
from app.predictor import predict
from app.publisher import publish_signal
from app.scheduler import start_scheduler
from app.grpc_server import serve as grpc_serve
from app.config import SUPPORTED_SYMBOLS, HOST, PORT, DATABASE_URL
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(
    title="ML Decision Engine",
    description="Generates buy/sell/hold signals using best models",
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

scheduler = None

def save_signal_to_db(symbol, signal, confidence, model, price, rsi=None):
    try:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO signals (symbol, signal, confidence, model, price, rsi, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (symbol, signal, confidence, model, price, rsi, 'ml-engine'))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[ML Engine] Failed to log signal: {e}")

@app.on_event("startup")
def startup():
    global scheduler
    scheduler = start_scheduler()
    # Start gRPC server in background thread
    import threading
    from app.grpc_server import serve as grpc_serve
    grpc_thread = threading.Thread(target=grpc_serve, daemon=False)
    grpc_thread.start()
    print("ML Decision Engine started with REST + gRPC servers!")

@app.on_event("shutdown")
def shutdown():
    global scheduler
    if scheduler:
        scheduler.shutdown()

class PredictRequest(BaseModel):
    symbol: str
    features: Dict[str, float]

@app.get("/health")
def health():
    return {"status": "ok", "service": "ml-decision-engine"}

@app.get("/symbols")
def get_symbols():
    return {"symbols": SUPPORTED_SYMBOLS}

@app.post("/predict")
def get_prediction(request: PredictRequest, publish: bool = True):
    if request.symbol not in SUPPORTED_SYMBOLS:
        raise HTTPException(
            status_code=400,
            detail=f"Symbol {request.symbol} not supported"
        )
    try:
        result = predict(request.symbol, request.features)
        save_signal_to_db(
            symbol=request.symbol,
            signal=result['signal'],
            confidence=result['confidence'],
            model=result['model'],
            price=request.features.get('close_lag_1', 0),
            rsi=request.features.get('rsi', None)
        )
        if publish:
            publish_signal({
                "symbol":     request.symbol,
                "signal":     result["signal"],
                "confidence": result["confidence"],
                "model":      result["model"],
                "timestamp":  datetime.datetime.utcnow().isoformat()
            })
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@app.post("/trigger-signals")
def trigger_signals():
    from app.scheduler import generate_and_publish_signals
    generate_and_publish_signals()
    return {"message": "Signals generated and published"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)




@app.get("/signal/{symbol}")
def get_signal(symbol: str):
    """Get current signal for a symbol — fetches candle internally"""
    symbol = symbol.replace("-", "/").upper()
    if symbol not in SUPPORTED_SYMBOLS:
        raise HTTPException(status_code=400, detail=f"Symbol {symbol} not supported")
    try:
        import grpc
        from app import market_data_pb2, market_data_pb2_grpc

        channel = grpc.insecure_channel('market-data-collector:50051')
        stub = market_data_pb2_grpc.MarketDataServiceStub(channel)

        # Get price
        price_resp = stub.GetPrice(
            market_data_pb2.PriceRequest(symbol=symbol.replace('/', '-')), timeout=5)
        price = float(price_resp.price)

        # Get candle + features
        ohlcv_resp = stub.GetOHLCV(
            market_data_pb2.OHLCVRequest(symbol=symbol.replace('/', '-'), limit=100), timeout=10)

        if not ohlcv_resp.candles:
            return {"signal": "UNKNOWN", "confidence": 0, "price": price}

        candle = ohlcv_resp.candles[-1]
        features = {
            'ma20': candle.ma20, 'ma50': candle.ma50, 'ma200': candle.ma200,
            'rsi': candle.rsi, 'returns': candle.returns, 'vol_20': candle.vol_20,
            'macd': candle.macd, 'macd_signal': candle.macd_signal,
            'macd_diff': candle.macd_diff,
            'bb_high': candle.bb_high, 'bb_low': candle.bb_low,
            'bb_mid': candle.bb_mid, 'bb_width': candle.bb_width,
            'bb_pct': candle.bb_pct, 'atr': candle.atr,
            'stoch_rsi': candle.stoch_rsi, 'stoch_rsi_k': candle.stoch_rsi_k,
            'stoch_rsi_d': candle.stoch_rsi_d,
            'volume_ratio': candle.volume_ratio,
            'dist_ma200': candle.dist_ma200, 'dist_ma50': candle.dist_ma50,
            'hour': candle.hour, 'day_of_week': candle.day_of_week,
            'close_lag_1': candle.close_lag_1, 'returns_lag_1': candle.returns_lag_1,
            'close_lag_2': candle.close_lag_2, 'returns_lag_2': candle.returns_lag_2,
            'close_lag_3': candle.close_lag_3, 'returns_lag_3': candle.returns_lag_3,
            'close_lag_6': candle.close_lag_6, 'returns_lag_6': candle.returns_lag_6,
            'close_lag_12': candle.close_lag_12, 'returns_lag_12': candle.returns_lag_12,
            'close_lag_24': candle.close_lag_24, 'returns_lag_24': candle.returns_lag_24,
        }

        result = predict(symbol, features)
        return {
            "signal": result["signal"],
            "confidence": result["confidence"],
            "model": result["model"],
            "price": price
        }
    except Exception as e:
        print(f"[ML Signal] Error: {e}")
        return {"signal": "ERROR", "confidence": 0, "price": 0, "error": str(e)}