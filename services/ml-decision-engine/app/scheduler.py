import grpc
import logging
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from app.config import SUPPORTED_SYMBOLS
from app.publisher import publish_signal
from app.predictor import predict
from app import market_data_pb2, market_data_pb2_grpc

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

MARKET_GRPC_CHANNEL = 'market-data-collector:50051'

def get_candles_grpc(symbol: str) -> list:
    """Fetch candles from market-data-collector via gRPC"""
    try:
        channel = grpc.insecure_channel(MARKET_GRPC_CHANNEL)
        stub = market_data_pb2_grpc.MarketDataServiceStub(channel)
        request = market_data_pb2.OHLCVRequest(
            symbol=symbol.replace('/', '-'),
            limit=100
        )
        response = stub.GetOHLCV(request, timeout=10)
        candles = []
        for c in response.candles:
            candles.append({
                'timestamp': c.timestamp,
                'open': c.open,
                'high': c.high,
                'low': c.low,
                'close': c.close,
                'volume': c.volume,
                'rsi': c.rsi,
                'ma20': c.ma20,
                'ma50': c.ma50,
                'ma200': c.ma200,
                'returns': c.returns,
                'vol_20': c.vol_20,
                'macd': c.macd,
                'macd_signal': c.macd_signal,
                'macd_diff': c.macd_diff,
                'bb_high': c.bb_high,
                'bb_low': c.bb_low,
                'bb_mid': c.bb_mid,
                'bb_width': c.bb_width,
                'bb_pct': c.bb_pct,
                'atr': c.atr,
                'stoch_rsi': c.stoch_rsi,
                'stoch_rsi_k': c.stoch_rsi_k,
                'stoch_rsi_d': c.stoch_rsi_d,
                'volume_ratio': c.volume_ratio,
                'dist_ma200': c.dist_ma200,
                'dist_ma50': c.dist_ma50,
                'hour': c.hour,
                'day_of_week': c.day_of_week,
                'close_lag_1': c.close_lag_1,
                'returns_lag_1': c.returns_lag_1,
                'close_lag_2': c.close_lag_2,
                'returns_lag_2': c.returns_lag_2,
                'close_lag_3': c.close_lag_3,
                'returns_lag_3': c.returns_lag_3,
                'close_lag_6': c.close_lag_6,
                'returns_lag_6': c.returns_lag_6,
                'close_lag_12': c.close_lag_12,
                'returns_lag_12': c.returns_lag_12,
                'close_lag_24': c.close_lag_24,
                'returns_lag_24': c.returns_lag_24,
            })
        return candles
    except Exception as e:
        print(f"[gRPC] Error fetching candles: {e}")
        return []

def generate_and_publish_signals():
    print(f"[Scheduler] Running signal generation at {datetime.datetime.utcnow()}")

    for symbol in SUPPORTED_SYMBOLS:
        try:
            candles = get_candles_grpc(symbol)

            if not candles:
                print(f"[Scheduler] No data for {symbol}")
                continue

            latest = candles[-1]
            features = {}
            for col in FEATURE_COLS:
                if col in latest:
                    features[col] = latest[col]

            if len(features) < 10:
                print(f"[Scheduler] Not enough features for {symbol}")
                continue

            result = predict(symbol, features)
            publish_signal({
                "symbol":     symbol,
                "signal":     result["signal"],
                "confidence": result["confidence"],
                "model":      result["model"],
                "timestamp":  datetime.datetime.utcnow().isoformat()
            })
            print(f"[Scheduler] Published {result['signal']} for {symbol} "
                  f"(confidence: {result['confidence']}%) via gRPC data")

        except Exception as e:
            print(f"[Scheduler] Error processing {symbol}: {e}")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        generate_and_publish_signals,
        trigger='interval',
        minutes=2,
        id='signal_generator',
        name='Generate and publish ML signals every 2 minutes',
        replace_existing=True
    )
    scheduler.start()
    print("[Scheduler] Started — signals will be published every 2 minutes")
    generate_and_publish_signals()
    return scheduler