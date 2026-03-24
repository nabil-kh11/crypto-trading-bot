import ccxt
import pandas as pd
import ta

def fetch_binance_historical_ohlcv(symbol="BTC/USDT", timeframe="1h", total_bars=10000):
    binance = ccxt.binance()
    limit = 1000
    all_ohlcv = []
    since = None
    # Start from the oldest data
    if since is None:
        # Go back in history: Set since to now - total_bars*bar_length
        now_ms = binance.milliseconds()
        bar_ms = 3600 * 1000 if timeframe.endswith("h") else 24 * 3600 * 1000
        since = now_ms - (total_bars * bar_ms)
    while len(all_ohlcv) < total_bars:
        ohlcv = binance.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
        if not ohlcv or len(ohlcv) == 0:
            break
        all_ohlcv.extend(ohlcv)
        print(f"Fetched {len(ohlcv)} bars, total so far: {len(all_ohlcv)}")
        since = ohlcv[-1][0] + 1  # move to bar after last returned
        if len(ohlcv) < limit:
            break
    # Remove duplicates
    df = pd.DataFrame(all_ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df.drop_duplicates(subset=["timestamp"], inplace=True)
    # Slice in case more than needed
    df = df.sort_values("timestamp").reset_index(drop=True)
    df = df.iloc[-total_bars:]
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

    # Add technical indicators
    df["ma20"] = df["close"].rolling(20).mean()
    df["ma50"] = df["close"].rolling(50).mean()
    df["rsi"] = ta.momentum.RSIIndicator(df["close"]).rsi()
    df["returns"] = df["close"].pct_change()
    df["vol_20"] = df["close"].rolling(20).std()

    # Save CSV
    csv_name = f"{symbol.replace('/', '_')}_ohlcv_{timeframe}_{len(df)}_with_indicators.csv"
    df.to_csv(csv_name, index=False)
    print(f"Saved {len(df)} bars for {symbol} ({timeframe}) with indicators as {csv_name}")

    # Save Excel
    excel_name = f"{symbol.replace('/', '_')}_ohlcv_{timeframe}_{len(df)}_with_indicators.xlsx"
    df.to_excel(excel_name, index=False, engine='openpyxl')
    print(f"Saved Excel as {excel_name}")

if __name__ == "__main__":
    pairs = ["BTC/USDT", "ETH/USDT"]
    for pair in pairs:
        fetch_binance_historical_ohlcv(symbol=pair, timeframe="1h", total_bars=10000)