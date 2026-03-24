import joblib
import numpy as np
import pandas as pd
from app.config import BTC_MODEL_PATH, ETH_MODEL_PATH, FEATURE_COLS

# Load models at startup
btc_model = joblib.load(BTC_MODEL_PATH)
eth_model = joblib.load(ETH_MODEL_PATH)

LABEL_MAP = {0: "SELL", 1: "HOLD", 2: "BUY"}

def predict(symbol: str, features: dict) -> dict:
    # Select correct model
    model = btc_model if "BTC" in symbol else eth_model

    # Build feature dataframe
    df = pd.DataFrame([features])

    # Make sure all features are present
    missing = [f for f in FEATURE_COLS if f not in df.columns]
    if missing:
        raise ValueError(f"Missing features: {missing}")

    X = df[FEATURE_COLS]

    # Predict
    prediction = model.predict(X)[0]
    probabilities = model.predict_proba(X)[0]

    return {
        "symbol": symbol,
        "signal": LABEL_MAP[prediction],
        "confidence": round(float(max(probabilities)) * 100, 2),
        "probabilities": {
            "SELL": round(float(probabilities[0]) * 100, 2),
            "HOLD": round(float(probabilities[1]) * 100, 2),
            "BUY":  round(float(probabilities[2]) * 100, 2),
        }
    }