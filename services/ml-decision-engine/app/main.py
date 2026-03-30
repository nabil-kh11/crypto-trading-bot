import uvicorn
import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
from app.predictor import predict
from app.publisher import publish_signal
from app.scheduler import start_scheduler
from app.config import SUPPORTED_SYMBOLS, HOST, PORT

app = FastAPI(
    title="ML Decision Engine",
    description="Generates buy/sell/hold signals using best models",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scheduler = None

@app.on_event("startup")
def startup():
    global scheduler
    scheduler = start_scheduler()
    print("ML Decision Engine started with hourly scheduler!")

@app.on_event("shutdown")
def shutdown():
    global scheduler
    if scheduler:
        scheduler.shutdown()
        print("Scheduler stopped!")

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
    """Manually trigger signal generation — useful for testing"""
    from app.scheduler import generate_and_publish_signals
    generate_and_publish_signals()
    return {"message": "Signals generated and published to queue"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)