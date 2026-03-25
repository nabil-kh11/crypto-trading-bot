import joblib
import numpy as np
import pandas as pd
from app.config import BTC_MODEL_PATH, ETH_MODEL_PATH, BTC_SCALER_PATH, FEATURE_COLS

# Load models and scaler at startup
btc_model  = joblib.load(BTC_MODEL_PATH)   # Neural Network
eth_model  = joblib.load(ETH_MODEL_PATH)   # Random Forest
btc_scaler = joblib.load(BTC_SCALER_PATH)  # Scaler for BTC only

LABEL_MAP = {0: "SELL", 1: "HOLD", 2: "BUY"}

def predict(symbol: str, features: dict) -> dict:
    missing = [f for f in FEATURE_COLS if f not in features]
    if missing:
        raise ValueError(f"Missing features: {missing}")

    df = pd.DataFrame([features])[FEATURE_COLS]

    if "BTC" in symbol:
        # Neural Network needs scaled features
        X = btc_scaler.transform(df)
        prediction = btc_model.predict(X)[0]
        probabilities = btc_model.predict_proba(X)[0]
    else:
        # Random Forest uses raw features
        X = df.values
        prediction = eth_model.predict(X)[0]
        probabilities = eth_model.predict_proba(X)[0]

    return {
        "symbol": symbol,
        "model": "Neural Network" if "BTC" in symbol else "Random Forest",
        "signal": LABEL_MAP[int(prediction)],
        "confidence": round(float(max(probabilities)) * 100, 2),
        "probabilities": {
            "SELL": round(float(probabilities[0]) * 100, 2),
            "HOLD": round(float(probabilities[1]) * 100, 2),
            "BUY":  round(float(probabilities[2]) * 100, 2),
        }
    }