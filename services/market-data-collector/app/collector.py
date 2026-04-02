import ccxt
import pandas as pd
import ta
from datetime import datetime
from app.config import TIMEFRAME, FETCH_LIMIT

# Always use public endpoints - no API key needed for OHLCV data
exchange = ccxt.binance()

def fetch_ohlcv(symbol: str, limit: int = FETCH_LIMIT) -> pd.DataFrame:
    # Need at least 250 candles for ma200 + all indicators
    actual_limit = max(limit, 300)
    raw = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=actual_limit)
    df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = _add_indicators(df)
    df = df.dropna()
    df = df.reset_index(drop=True)
    # Return only requested number of rows
    return df.tail(limit).reset_index(drop=True)

def _add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    # Original indicators
    df["ma20"]    = df["close"].rolling(20).mean()
    df["ma50"]    = df["close"].rolling(50).mean()
    df["ma200"]   = df["close"].rolling(200).mean()  # NEW
    df["rsi"]     = ta.momentum.RSIIndicator(df["close"]).rsi()
    df["returns"] = df["close"].pct_change()
    df["vol_20"]  = df["close"].rolling(20).std()

    # MACD
    macd = ta.trend.MACD(df["close"])
    df["macd"]        = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["macd_diff"]   = macd.macd_diff()

    # Bollinger Bands
    bb = ta.volatility.BollingerBands(df["close"])
    df["bb_high"]  = bb.bollinger_hband()
    df["bb_low"]   = bb.bollinger_lband()
    df["bb_mid"]   = bb.bollinger_mavg()
    df["bb_width"] = (df["bb_high"] - df["bb_low"]) / df["bb_mid"]
    df["bb_pct"]   = (df["close"] - df["bb_low"]) / (df["bb_high"] - df["bb_low"])  # NEW

    # ATR
    df["atr"] = ta.volatility.AverageTrueRange(
                    df["high"], df["low"], df["close"]).average_true_range()

    # Stochastic RSI
    stoch = ta.momentum.StochRSIIndicator(df["close"])
    df["stoch_rsi"]   = stoch.stochrsi()
    df["stoch_rsi_k"] = stoch.stochrsi_k()
    df["stoch_rsi_d"] = stoch.stochrsi_d()

    # Volume indicators — NEW
    df["volume_ma20"]  = df["volume"].rolling(20).mean()
    df["volume_ratio"] = df["volume"] / df["volume_ma20"]

    # Price position — NEW
    df["dist_ma200"] = (df["close"] - df["ma200"]) / df["ma200"]
    df["dist_ma50"]  = (df["close"] - df["ma50"])  / df["ma50"]

    # Time features — NEW
    df["hour"]        = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek

    # Lag features
    for lag in [1, 2, 3, 6, 12, 24]:
        df[f"close_lag_{lag}"]   = df["close"].shift(lag)
        df[f"returns_lag_{lag}"] = df["returns"].shift(lag)

    return df

def get_latest_price(symbol: str) -> dict:
    ticker = exchange.fetch_ticker(symbol)
    return {
        "symbol":    symbol,
        "price":     ticker["last"],
        "high":      ticker["high"],
        "low":       ticker["low"],
        "volume":    ticker["quoteVolume"],
        "timestamp": datetime.utcnow().isoformat(),
    }