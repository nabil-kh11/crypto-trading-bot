import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv('/app/.env')

SUPPORTED_SYMBOLS = ["BTC/USDT", "ETH/USDT"]
TIMEFRAME   = "1h"
FETCH_LIMIT = 1000
HOST        = os.getenv("HOST", "0.0.0.0")
PORT        = int(os.getenv("PORT", 8001))