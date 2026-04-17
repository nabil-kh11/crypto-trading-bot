import grpc
import logging
import datetime
import threading
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

def process_candle(symbol: str, candle) -> None:
    """Process a single candle and publish signal"""
    try:
        features = {
            'ma20': candle.ma20, 'ma50': candle.ma50, 'ma200': candle.ma200,
            'rsi': candle.rsi, 'returns': candle.returns, 'vol_20': candle.vol_20,
            'macd': candle.macd, 'macd_signal': candle.macd_signal,
            'macd_diff': candle.macd_diff,
            'bb_high': candle.bb_high, 'bb_low': candle.bb_low,
            'bb_mid': candle.bb_mid, 'bb_width': candle.bb_width,
            'bb_pct': candle.bb_pct, 'atr': candle.atr,
            'stoch_rsi': candle.stoch_rsi, 'stoch_rsi_k': candle.stoch_rsi_k,
            'stoch_rsi_d': candle.stoch_rsi_d,
            'volume_ratio': candle.volume_ratio,
            'dist_ma200': candle.dist_ma200, 'dist_ma50': candle.dist_ma50,
            'hour': candle.hour, 'day_of_week': candle.day_of_week,
            'close_lag_1': candle.close_lag_1, 'returns_lag_1': candle.returns_lag_1,
            'close_lag_2': candle.close_lag_2, 'returns_lag_2': candle.returns_lag_2,
            'close_lag_3': candle.close_lag_3, 'returns_lag_3': candle.returns_lag_3,
            'close_lag_6': candle.close_lag_6, 'returns_lag_6': candle.returns_lag_6,
            'close_lag_12': candle.close_lag_12, 'returns_lag_12': candle.returns_lag_12,
            'close_lag_24': candle.close_lag_24, 'returns_lag_24': candle.returns_lag_24,
        }

        if len([v for v in features.values() if v != 0]) < 10:
            print(f"[Stream] Not enough features for {symbol}")
            return

        result = predict(symbol, features)
        publish_signal({
            "symbol":     symbol,
            "signal":     result["signal"],
            "confidence": result["confidence"],
            "model":      result["model"],
            "timestamp":  datetime.datetime.utcnow().isoformat()
        })
        print(f"[Stream] Published {result['signal']} for {symbol} "
              f"({result['confidence']:.1f}%) via gRPC stream")

    except Exception as e:
        print(f"[Stream] Error processing candle for {symbol}: {e}")

def stream_candles_for_symbol(symbol: str) -> None:
    """Stream candles from market-data-collector for one symbol"""
    print(f"[Stream] Starting stream for {symbol}")
    while True:
        try:
            channel = grpc.insecure_channel(MARKET_GRPC_CHANNEL)
            stub = market_data_pb2_grpc.MarketDataServiceStub(channel)
            request = market_data_pb2.StreamRequest(
                symbol=symbol.replace('/', '-'),
                interval_seconds=3600
            )
            print(f"[Stream] Connected to market-data-collector for {symbol}")
            for candle in stub.StreamCandles(request):
                process_candle(symbol, candle)
        except Exception as e:
            print(f"[Stream] Connection lost for {symbol}: {e} — reconnecting in 10s")
            import time
            time.sleep(10)

def generate_and_publish_signals():
    """Legacy function kept for manual trigger via API"""
    print(f"[Scheduler] Manual signal generation at {datetime.datetime.utcnow()}")
    for symbol in SUPPORTED_SYMBOLS:
        try:
            channel = grpc.insecure_channel(MARKET_GRPC_CHANNEL)
            stub = market_data_pb2_grpc.MarketDataServiceStub(channel)
            request = market_data_pb2.OHLCVRequest(
                symbol=symbol.replace('/', '-'),
                limit=100
            )
            response = stub.GetOHLCV(request, timeout=10)
            if not response.candles:
                continue
            latest = response.candles[-1]
            features = {}
            for col in FEATURE_COLS:
                features[col] = getattr(latest, col, 0)
            result = predict(symbol, features)
            publish_signal({
                "symbol":     symbol,
                "signal":     result["signal"],
                "confidence": result["confidence"],
                "model":      result["model"],
                "timestamp":  datetime.datetime.utcnow().isoformat()
            })
            print(f"[Scheduler] Published {result['signal']} for {symbol}")
        except Exception as e:
            print(f"[Scheduler] Error for {symbol}: {e}")

def start_scheduler():
    """Start gRPC streaming threads for each symbol"""
    for symbol in SUPPORTED_SYMBOLS:
        t = threading.Thread(
            target=stream_candles_for_symbol,
            args=(symbol,),
            daemon=True,
            name=f"stream-{symbol}"
        )
        t.start()
        print(f"[Stream] Thread started for {symbol}")

    print("[Stream] gRPC streaming started for all symbols — real-time signals!")
    
    # Generate initial signals immediately
    generate_and_publish_signals()
    
    return None