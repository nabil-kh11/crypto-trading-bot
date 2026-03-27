import os
from dotenv import load_dotenv

load_dotenv()

BTC_MODEL_PATH   = os.getenv("BTC_MODEL_PATH",   "../../data/models/best_btc.joblib")
ETH_MODEL_PATH   = os.getenv("ETH_MODEL_PATH",   "../../data/models/best_eth.joblib")
BTC_SCALER_PATH  = os.getenv("BTC_SCALER_PATH",  "../../data/models/best_btc_scaler.joblib")

SUPPORTED_SYMBOLS = ["BTC/USDT", "ETH/USDT"]

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

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8002))
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
QUEUE_NAME   = "trading_signals"