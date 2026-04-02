import requests
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from app.config import MARKET_DATA_URL, SUPPORTED_SYMBOLS
from app.publisher import publish_signal
from app.predictor import predict
import datetime

logger = logging.getLogger(__name__)

FEATURE_COLS = [
    'ma20', 'ma50', 'ma200', 'rsi', 'returns', 'vol_20',
    'macd', 'macd_signal', 'macd_diff',
    'bb_high', 'bb_low', 'bb_mid', 'bb_width', 'bb_pct',
    'atr', 'stoch_rsi', 'stoch_rsi_k', 'stoch_rsi_d',
    'volume_ratio', 'dist_ma200', 'dist_ma50',
    'hour', 'day_of_week',
    'close_lag_1', 'returns_lag_1',
    'close_lag_2', 'returns_lag_2',
    'close_lag_3', 'returns_lag_3',
    'close_lag_6', 'returns_lag_6',
    'close_lag_12', 'returns_lag_12',
    'close_lag_24', 'returns_lag_24'
]

def generate_and_publish_signals():
    """Fetch latest data, generate ML signals and publish to RabbitMQ"""
    print(f"[Scheduler] Running signal generation at {datetime.datetime.utcnow()}")
    
    for symbol in SUPPORTED_SYMBOLS:
        try:
            symbol_url = symbol.replace("/", "-")
            response = requests.get(
                f"{MARKET_DATA_URL}/ohlcv/{symbol_url}?limit=100", 
                timeout=10
            )
            candles = response.json()
            
            if not candles or len(candles) == 0:
                print(f"[Scheduler] No data for {symbol}")
                continue

            latest = candles[-1]
            features = {}
            for col in FEATURE_COLS:
                if col in latest:
                    features[col] = latest[col]
                else:
                    print(f"[Scheduler] Missing feature {col} for {symbol}")
                    break
            else:
                result = predict(symbol, features)
                publish_signal({
                    "symbol":     symbol,
                    "signal":     result["signal"],
                    "confidence": result["confidence"],
                    "model":      result["model"],
                    "timestamp":  datetime.datetime.utcnow().isoformat()
                })
                print(f"[Scheduler] Published {result['signal']} for {symbol} "
                      f"(confidence: {result['confidence']}%)")

        except Exception as e:
            print(f"[Scheduler] Error processing {symbol}: {e}")

def start_scheduler():
    scheduler = BackgroundScheduler()
    
    # Run every hour
    scheduler.add_job(
        generate_and_publish_signals,
        trigger='interval',
        minutes=1,
        id='signal_generator',
        name='Generate and publish ML signals every 1 minutes',
        replace_existing=True
    )
    
    scheduler.start()
    print("[Scheduler] Started — signals will be published every 1 minutes")
    
    # Run immediately on startup
    generate_and_publish_signals()
    
    return scheduler