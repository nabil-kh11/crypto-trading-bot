import ccxt
import pandas as pd
import ta
import time
from datetime import datetime

exchange = ccxt.binance()

def fetch_large_dataset(symbol: str, timeframe: str = '1h', total_candles: int = 50000):
    print(f"Fetching {total_candles} candles for {symbol}...")
    
    all_candles = []
    # Start from 6 years ago
    since = exchange.parse8601('2019-01-01T00:00:00Z')
    batch_size = 1000
    
    while len(all_candles) < total_candles:
        try:
            candles = exchange.fetch_ohlcv(
                symbol,
                timeframe,
                since=since,
                limit=batch_size
            )
            if not candles:
                break
            all_candles.extend(candles)
            since = candles[-1][0] + 1
            print(f"  Fetched {len(all_candles)} candles...")
            time.sleep(0.5)
            if len(candles) < batch_size:
                print("  Reached end of available data")
                break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(2)
            continue

    df = pd.DataFrame(all_candles[:total_candles],
                      columns=['timestamp','open','high','low','close','volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df.sort_values('timestamp').reset_index(drop=True)
    df = df.drop_duplicates(subset='timestamp').reset_index(drop=True)
    print(f"  Total: {len(df)} candles")
    print(f"  From: {df['timestamp'].iloc[0]}")
    print(f"  To:   {df['timestamp'].iloc[-1]}")
    return df

def add_indicators(df):
    df['ma20']    = df['close'].rolling(20).mean()
    df['ma50']    = df['close'].rolling(50).mean()
    df['ma200']   = df['close'].rolling(200).mean()
    df['rsi']     = ta.momentum.RSIIndicator(df['close']).rsi()
    df['returns'] = df['close'].pct_change()
    df['vol_20']  = df['close'].rolling(20).std()

    macd = ta.trend.MACD(df['close'])
    df['macd']        = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_diff']   = macd.macd_diff()

    bb = ta.volatility.BollingerBands(df['close'])
    df['bb_high']  = bb.bollinger_hband()
    df['bb_low']   = bb.bollinger_lband()
    df['bb_mid']   = bb.bollinger_mavg()
    df['bb_width'] = (df['bb_high'] - df['bb_low']) / df['bb_mid']
    df['bb_pct']   = (df['close'] - df['bb_low']) / (df['bb_high'] - df['bb_low'])

    df['atr'] = ta.volatility.AverageTrueRange(
                    df['high'], df['low'], df['close']).average_true_range()

    stoch = ta.momentum.StochRSIIndicator(df['close'])
    df['stoch_rsi']   = stoch.stochrsi()
    df['stoch_rsi_k'] = stoch.stochrsi_k()
    df['stoch_rsi_d'] = stoch.stochrsi_d()

    df['volume_ma20']  = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_ma20']
    df['dist_ma200']   = (df['close'] - df['ma200']) / df['ma200']
    df['hour']         = df['timestamp'].dt.hour
    df['day_of_week']  = df['timestamp'].dt.dayofweek

    for lag in [1, 2, 3, 6, 12, 24]:
        df[f'close_lag_{lag}']   = df['close'].shift(lag)
        df[f'returns_lag_{lag}'] = df['returns'].shift(lag)

    df = df.dropna().reset_index(drop=True)
    return df

# Save path — absolute path
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR  = os.path.join(BASE_DIR, 'data', 'raw')

print("="*60)
print("Fetching large historical dataset")
print(f"Saving to: {RAW_DIR}")
print("="*60)

for symbol in ['BTC/USDT', 'ETH/USDT']:
    symbol_clean = symbol.replace('/', '_')
    df = fetch_large_dataset(symbol, timeframe='1h', total_candles=63000)
    df = add_indicators(df)
    filename = os.path.join(RAW_DIR, f'{symbol_clean}_ohlcv_1h_50000_with_indicators.csv')
    df.to_csv(filename, index=False)
    print(f"\n✓ Saved {len(df)} rows to {filename}")
    print(f"  Columns: {len(df.columns)}")
    print(f"  Range: {df['timestamp'].iloc[0]} → {df['timestamp'].iloc[-1]}")

print("\nDone!")