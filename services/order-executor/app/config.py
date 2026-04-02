import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parents[3] / '.env')

# RabbitMQ
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
QUEUE_NAME   = "trading_signals"

# PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:admin@localhost:5432/cryptobot")

# ML Decision Engine
ML_ENGINE_URL = os.getenv("ML_ENGINE_URL", "http://localhost:8002")

# Market Data Collector
MARKET_DATA_URL = os.getenv("MARKET_DATA_URL", "http://localhost:8001")

# Binance Testnet
BINANCE_TESTNET_API_KEY    = os.getenv("BINANCE_TESTNET_API_KEY", "")
BINANCE_TESTNET_SECRET_KEY = os.getenv("BINANCE_TESTNET_SECRET_KEY", "")
USE_TESTNET                = os.getenv("USE_TESTNET", "true").lower() == "true"

# Trading settings
INITIAL_CAPITAL = float(os.getenv("INITIAL_CAPITAL", "10000.0"))
STOP_LOSS_PCT   = float(os.getenv("STOP_LOSS_PCT", "0.05"))
MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "0.0"))


# Service
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8004))