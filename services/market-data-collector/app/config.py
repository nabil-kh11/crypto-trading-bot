import os
from dotenv import load_dotenv

load_dotenv()

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY", "")

SYMBOLS = ["BTC/USDT", "ETH/USDT"]
TIMEFRAME = "1h"
FETCH_LIMIT = 1000

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8001))