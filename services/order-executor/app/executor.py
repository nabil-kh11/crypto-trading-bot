import requests
from datetime import datetime
from app.config import (ML_ENGINE_URL, MARKET_DATA_URL,
                        INITIAL_CAPITAL, STOP_LOSS_PCT, MIN_CONFIDENCE)
from app.database import get_portfolio, update_portfolio, save_trade

FEATURE_COLS = [
    'ma20', 'ma50', 'rsi', 'returns', 'vol_20',
    'macd', 'macd_signal', 'macd_diff',
    'bb_high', 'bb_low', 'bb_mid', 'bb_width',
    'atr', 'stoch_rsi', 'stoch_rsi_k', 'stoch_rsi_d',
    'close_lag_1', 'returns_lag_1',
    'close_lag_2', 'returns_lag_2',
    'close_lag_3', 'returns_lag_3',
    'close_lag_6', 'returns_lag_6',
    'close_lag_12', 'returns_lag_12',
    'close_lag_24', 'returns_lag_24'
]

def get_latest_price(symbol: str) -> float:
    symbol_url = symbol.replace("/", "-")
    response = requests.get(f"{MARKET_DATA_URL}/price/{symbol_url}", timeout=5)
    data = response.json()
    return float(data["price"])

def get_ml_signal(symbol: str) -> dict:
    symbol_url = symbol.replace("/", "-")
    response = requests.get(
        f"{MARKET_DATA_URL}/ohlcv/{symbol_url}?limit=100", timeout=10)
    candles = response.json()
    if not candles:
        return None

    latest = candles[-1]

    features = {}
    for col in FEATURE_COLS:
        if col in latest:
            features[col] = latest[col]
        else:
            print(f"Missing feature: {col}")
            return None

    response = requests.post(f"{ML_ENGINE_URL}/predict", json={
        "symbol": symbol,
        "features": features
    }, timeout=10)
    return response.json()

def execute_trade(symbol: str) -> dict:
    portfolio = get_portfolio(symbol)
    if not portfolio:
        update_portfolio(symbol, INITIAL_CAPITAL, 0.0, 0.0)
        portfolio = get_portfolio(symbol)

    capital   = portfolio['capital']
    position  = portfolio['position']
    avg_price = portfolio['avg_price']

    try:
        signal_data = get_ml_signal(symbol)
        if not signal_data:
            return {"status": "error", "message": "Could not get ML signal"}

        signal     = signal_data['signal']
        confidence = signal_data['confidence']
        price      = get_latest_price(symbol)

    except Exception as e:
        return {"status": "error", "message": str(e)}

    if confidence < MIN_CONFIDENCE:
        return {
            "status": "skipped",
            "reason": f"Confidence {confidence}% below threshold {MIN_CONFIDENCE}%",
            "signal": signal,
            "price":  price
        }

    if signal == "BUY" and capital > 0:
        quantity = capital / price
        trade = {
            "symbol":         symbol,
            "signal":         signal,
            "confidence":     confidence,
            "price":          price,
            "quantity":       quantity,
            "capital_before": capital,
            "capital_after":  0.0,
            "position_value": quantity * price,
            "trade_type":     "PAPER",
            "status":         "EXECUTED"
        }
        update_portfolio(symbol, 0.0, quantity, price)
        save_trade(trade)

    elif signal == "SELL" and position > 0:
        capital_after = position * price
        trade = {
            "symbol":         symbol,
            "signal":         signal,
            "confidence":     confidence,
            "price":          price,
            "quantity":       position,
            "capital_before": 0.0,
            "capital_after":  capital_after,
            "position_value": 0.0,
            "trade_type":     "PAPER",
            "status":         "EXECUTED"
        }
        update_portfolio(symbol, capital_after, 0.0, 0.0)
        save_trade(trade)

    else:
        return {
            "status":     "hold",
            "signal":     signal,
            "confidence": confidence,
            "price":      price,
            "capital":    capital,
            "position":   position
        }

    return {
        "status":    "executed",
        "trade":     trade,
        "portfolio": get_portfolio(symbol)
    }