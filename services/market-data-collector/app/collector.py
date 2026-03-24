import ccxt
import pandas as pd
import ta
from datetime import datetime
from app.config import BINANCE_API_KEY, BINANCE_SECRET_KEY, TIMEFRAME, FETCH_LIMIT

exchange = ccxt.binance({
    "apiKey": BINANCE_API_KEY,
    "secret": BINANCE_SECRET_KEY,
})

def fetch_ohlcv(symbol: str, limit: int = FETCH_LIMIT) -> pd.DataFrame:
    raw = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=limit)
    df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = _add_indicators(df)
    df = df.dropna()
    df = df.reset_index(drop=True)
    return df

def _add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df["ma20"]    = df["close"].rolling(20).mean()
    df["ma50"]    = df["close"].rolling(50).mean()
    df["rsi"]     = ta.momentum.RSIIndicator(df["close"]).rsi()
    df["macd"]    = ta.trend.MACD(df["close"]).macd()
    df["bb_high"] = ta.volatility.BollingerBands(df["close"]).bollinger_hband()
    df["bb_low"]  = ta.volatility.BollingerBands(df["close"]).bollinger_lband()
    df["returns"] = df["close"].pct_change()
    df["vol_20"]  = df["close"].rolling(20).std()
    return df

def get_latest_price(symbol: str) -> dict:
    ticker = exchange.fetch_ticker(symbol)
    return {
        "symbol": symbol,
        "price": ticker["last"],
        "high": ticker["high"],
        "low": ticker["low"],
        "volume": ticker["quoteVolume"],
        "timestamp": datetime.utcnow().isoformat(),
    }