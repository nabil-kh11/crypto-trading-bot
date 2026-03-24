import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
from app.predictor import predict
from app.config import SUPPORTED_SYMBOLS, HOST, PORT

app = FastAPI(
    title="ML Decision Engine",
    description="Generates buy/sell/hold signals using XGBoost models",
    version="1.0.0"
)

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
def get_prediction(request: PredictRequest):
    if request.symbol not in SUPPORTED_SYMBOLS:
        raise HTTPException(
            status_code=400,
            detail=f"Symbol {request.symbol} not supported"
        )
    try:
        result = predict(request.symbol, request.features)
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)