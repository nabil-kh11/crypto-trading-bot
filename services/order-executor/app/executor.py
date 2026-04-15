import grpc
from datetime import datetime, timedelta
from app.config import (ML_ENGINE_URL, MARKET_DATA_URL,
                        MIN_CONFIDENCE, USE_TESTNET)
from app.database import save_trade, get_avg_buy_price, get_last_buy_time
from app.binance_executor import (place_market_buy, place_market_sell,
                                   get_testnet_balance)
from app import ml_engine_pb2, ml_engine_pb2_grpc
from app import market_data_pb2, market_data_pb2_grpc

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

# ── STRATEGY PARAMETERS ────────────────────────────────────────────────────
STOP_LOSS_PCT        = 0.05   # 5% stop loss
TRAILING_STOP_PCT    = 0.03   # 3% trailing stop
TAKE_PROFIT_1        = 0.10   # 10% → sell 30%
TAKE_PROFIT_2        = 0.15   # 15% → sell 50%
TAKE_PROFIT_3        = 0.20   # 20% → sell 100%
MIN_HOLD_HOURS       = 4      # minimum hold time
RSI_OVERBOUGHT       = 70
RSI_OVERSOLD         = 30
MAX_PORTFOLIO_HEAT   = 0.40   # max 40% of capital at risk
MAX_DAILY_LOSS_PCT   = 0.10   # stop trading if -10% today
BASE_RISK_PCT        = 0.02   # base risk per trade 2%
MAX_RISK_PCT         = 0.20   # max risk per trade 20%
ATR_MULTIPLIER       = 2.0    # ATR-based stop distance

# gRPC channels
ML_GRPC_CHANNEL     = 'ml-decision-engine:50052'
MARKET_GRPC_CHANNEL = 'market-data-collector:50051'

# Track highest price for trailing stop
_highest_prices = {}
_daily_start_balance = {}
_daily_losses = {}

def get_latest_price(symbol: str) -> float:
    channel = grpc.insecure_channel(MARKET_GRPC_CHANNEL)
    stub = market_data_pb2_grpc.MarketDataServiceStub(channel)
    request = market_data_pb2.PriceRequest(symbol=symbol.replace('/', '-'))
    response = stub.GetPrice(request, timeout=5)
    print(f"[gRPC] Price {symbol}: {response.price}")
    return float(response.price)

def get_latest_candle(symbol: str) -> dict:
    channel = grpc.insecure_channel(MARKET_GRPC_CHANNEL)
    stub = market_data_pb2_grpc.MarketDataServiceStub(channel)
    request = market_data_pb2.OHLCVRequest(
        symbol=symbol.replace('/', '-'),
        limit=100
    )
    response = stub.GetOHLCV(request, timeout=10)
    if not response.candles:
        return None
    latest = response.candles[-1]
    print(f"[gRPC] Got candle for {symbol}")
    return {
        'timestamp': latest.timestamp,
        'open': latest.open, 'high': latest.high,
        'low': latest.low, 'close': latest.close,
        'volume': latest.volume, 'rsi': latest.rsi,
        'ma20': latest.ma20, 'ma50': latest.ma50, 'ma200': latest.ma200,
        'returns': latest.returns, 'vol_20': latest.vol_20,
        'macd': latest.macd, 'macd_signal': latest.macd_signal,
        'macd_diff': latest.macd_diff,
        'bb_high': latest.bb_high, 'bb_low': latest.bb_low,
        'bb_mid': latest.bb_mid, 'bb_width': latest.bb_width,
        'bb_pct': latest.bb_pct, 'atr': latest.atr,
        'stoch_rsi': latest.stoch_rsi, 'stoch_rsi_k': latest.stoch_rsi_k,
        'stoch_rsi_d': latest.stoch_rsi_d,
        'volume_ratio': latest.volume_ratio,
        'dist_ma200': latest.dist_ma200, 'dist_ma50': latest.dist_ma50,
        'hour': latest.hour, 'day_of_week': latest.day_of_week,
        'close_lag_1': latest.close_lag_1, 'returns_lag_1': latest.returns_lag_1,
        'close_lag_2': latest.close_lag_2, 'returns_lag_2': latest.returns_lag_2,
        'close_lag_3': latest.close_lag_3, 'returns_lag_3': latest.returns_lag_3,
        'close_lag_6': latest.close_lag_6, 'returns_lag_6': latest.returns_lag_6,
        'close_lag_12': latest.close_lag_12, 'returns_lag_12': latest.returns_lag_12,
        'close_lag_24': latest.close_lag_24, 'returns_lag_24': latest.returns_lag_24,
    }

def get_ml_signal(symbol: str, candle: dict) -> dict:
    features = {}
    for col in FEATURE_COLS:
        if col in candle:
            features[col] = float(candle[col])
    if len(features) < 10:
        return None
    channel = grpc.insecure_channel(ML_GRPC_CHANNEL)
    stub = ml_engine_pb2_grpc.MLEngineServiceStub(channel)
    request = ml_engine_pb2.PredictRequest(
        symbol=symbol, features=features, publish=False
    )
    response = stub.Predict(request, timeout=10)
    print(f"[gRPC] Signal: {response.signal} ({response.confidence:.1f}%)")
    return {
        'signal': response.signal,
        'confidence': response.confidence,
        'model': response.model
    }

def get_sentiment_score(symbol: str) -> float:
    """Get FinBERT sentiment score for symbol"""
    try:
        asset = symbol.split('/')[0]
        resp = requests.get(
            f"http://sentiment-collector:8003/summary/{asset}",
            timeout=5
        )
        data = resp.json()
        return float(data.get('avg_score', 0.0))
    except Exception as e:
        print(f"[Sentiment] Error: {e}")
        return 0.0

def kelly_criterion(confidence: float, win_rate: float = 0.55) -> float:
    """
    Kelly Criterion: f = (bp - q) / b
    b = odds (confidence/100), p = win probability, q = 1-p
    Returns optimal fraction of capital to invest
    """
    p = win_rate
    q = 1 - p
    b = confidence / 100
    kelly = (b * p - q) / b
    # Use half-Kelly for safety
    half_kelly = kelly / 2
    return max(0, min(half_kelly, MAX_RISK_PCT))

def calculate_volatility_factor(atr: float, price: float) -> float:
    """
    Reduce position size when volatility is high
    ATR/Price ratio: higher = more volatile = smaller position
    """
    if price <= 0 or atr <= 0:
        return 1.0
    atr_pct = atr / price
    if atr_pct > 0.05:      # > 5% ATR → high volatility
        return 0.5
    elif atr_pct > 0.03:    # > 3% ATR → medium volatility
        return 0.75
    else:                   # < 3% ATR → low volatility
        return 1.0

def check_max_daily_loss(symbol: str, current_balance: float) -> bool:
    """
    Returns True if daily loss limit reached (stop trading)
    """
    today = datetime.utcnow().date().isoformat()
    key = f"{symbol}_{today}"
    if key not in _daily_start_balance:
        _daily_start_balance[key] = current_balance
        return False
    start = _daily_start_balance[key]
    if start <= 0:
        return False
    loss_pct = (start - current_balance) / start
    if loss_pct >= MAX_DAILY_LOSS_PCT:
        print(f"[RiskMgmt] Daily loss limit reached: {loss_pct*100:.1f}% — STOP TRADING")
        return True
    return False

def calculate_buy_size(
    usdt_balance: float,
    confidence: float,
    candle: dict = None
) -> float:
    """
    Position sizing using:
    1. Kelly Criterion (optimal bet size)
    2. ATR volatility adjustment
    """
    if confidence < 50:
        return 0

    # Kelly Criterion base position
    kelly_pct = kelly_criterion(confidence)

    # ATR volatility adjustment
    atr = candle.get('atr', 0) if candle else 0
    price = candle.get('close', 1) if candle else 1
    vol_factor = calculate_volatility_factor(atr, price)

    # Final position size
    position_pct = kelly_pct * vol_factor
    position_pct = max(BASE_RISK_PCT, min(position_pct, MAX_RISK_PCT))
    position_size = usdt_balance * position_pct

    print(f"[Strategy] Kelly={kelly_pct*100:.1f}% "
          f"VolFactor={vol_factor:.2f} "
          f"→ invest {position_pct*100:.1f}% = ${position_size:.2f}")

    return round(position_size, 2)

def calculate_sell_size(
    asset_balance: float,
    confidence: float,
    avg_buy_price: float,
    current_price: float,
    symbol: str = ""
) -> float:
    """
    Tiered take-profit selling strategy:
    +10% → sell 30%
    +15% → sell 50%
    +20% → sell 100%
    Loss  → sell 10% (cut losses gradually)
    """
    if asset_balance <= 0:
        return 0

    pnl_pct = ((current_price - avg_buy_price) / avg_buy_price * 100) \
              if avg_buy_price > 0 else 0

    # Tiered take profit
    if pnl_pct >= TAKE_PROFIT_3 * 100:
        sell_pct = 1.0
        reason = f"Take Profit 3 (+{TAKE_PROFIT_3*100:.0f}%)"
    elif pnl_pct >= TAKE_PROFIT_2 * 100:
        sell_pct = 0.50
        reason = f"Take Profit 2 (+{TAKE_PROFIT_2*100:.0f}%)"
    elif pnl_pct >= TAKE_PROFIT_1 * 100:
        sell_pct = 0.30
        reason = f"Take Profit 1 (+{TAKE_PROFIT_1*100:.0f}%)"
    elif pnl_pct > 0:
        sell_pct = 0.25
        reason = "Small profit"
    else:
        sell_pct = 0.10
        reason = "Cut losses"

    sell_amount = asset_balance * sell_pct
    print(f"[Strategy] P&L={pnl_pct:.1f}% | {reason} "
          f"→ sell {sell_pct*100:.0f}% = {sell_amount:.6f}")
    return round(sell_amount, 6)

def check_stop_loss(
    avg_buy_price: float,
    current_price: float,
    symbol: str = ""
) -> bool:
    """
    Dual stop loss system:
    1. Fixed stop loss: -5% from entry
    2. Trailing stop loss: -3% from highest price reached
    """
    if avg_buy_price <= 0:
        return False

    # Update trailing stop tracker
    if symbol:
        if symbol not in _highest_prices:
            _highest_prices[symbol] = current_price
        elif current_price > _highest_prices[symbol]:
            _highest_prices[symbol] = current_price

    # Fixed stop loss
    drop_from_entry = (avg_buy_price - current_price) / avg_buy_price
    if drop_from_entry >= STOP_LOSS_PCT:
        print(f"[StopLoss] Fixed stop triggered! "
              f"drop={drop_from_entry*100:.1f}% from entry")
        return True

    # Trailing stop loss
    if symbol and symbol in _highest_prices:
        highest = _highest_prices[symbol]
        drop_from_high = (highest - current_price) / highest
        if drop_from_high >= TRAILING_STOP_PCT:
            print(f"[TrailingStop] Triggered! "
                  f"drop={drop_from_high*100:.1f}% from high ${highest:.2f}")
            if symbol in _highest_prices:
                del _highest_prices[symbol]
            return True

    return False

def check_multi_timeframe_trend(candle: dict, signal: str) -> bool:
    """
    Multi-timeframe trend confirmation using MA20/MA50/MA200
    BUY:  requires MA20 > MA50 > MA200 (strong uptrend)
    SELL: requires MA20 < MA50 (downtrend starting)
    """
    ma20  = candle.get('ma20', 0)
    ma50  = candle.get('ma50', 0)
    ma200 = candle.get('ma200', 0)

    if signal == 'BUY':
        if ma20 < ma50:
            print(f"[TrendFilter] BUY blocked — MA20 < MA50 (downtrend)")
            return False
        if ma50 < ma200:
            print(f"[TrendFilter] BUY allowed but weak — MA50 < MA200")
            # Allow but warn (not strong uptrend)
        return True

    if signal == 'SELL':
        if ma20 > ma50:
            print(f"[TrendFilter] SELL blocked — uptrend still active")
            return False
        return True

    return True

def check_trend_filter(candle: dict, signal: str) -> bool:
    return check_multi_timeframe_trend(candle, signal)

def check_rsi_filter(candle: dict, signal: str) -> bool:
    rsi = candle.get('rsi', 50)
    stoch_rsi = candle.get('stoch_rsi', 0.5)

    if signal == 'BUY':
        if rsi > RSI_OVERBOUGHT:
            print(f"[RSIFilter] BUY blocked — overbought RSI={rsi:.1f}")
            return False
        if stoch_rsi > 0.8:
            print(f"[RSIFilter] BUY blocked — StochRSI overbought={stoch_rsi:.2f}")
            return False
    if signal == 'SELL':
        if rsi < RSI_OVERSOLD:
            print(f"[RSIFilter] SELL blocked — oversold RSI={rsi:.1f}")
            return False

    return True

def check_volume_filter(candle: dict, signal: str) -> bool:
    """
    Only trade when volume is above average
    volume_ratio > 1.0 means above average volume
    """
    volume_ratio = candle.get('volume_ratio', 1.0)
    if volume_ratio < 0.8:
        print(f"[VolumeFilter] {signal} blocked — low volume ratio={volume_ratio:.2f}")
        return False
    return True

def check_min_hold_time(symbol: str) -> bool:
    last_buy = get_last_buy_time(symbol)
    if not last_buy:
        return True
    hours_held = (datetime.utcnow() - last_buy).total_seconds() / 3600
    if hours_held < MIN_HOLD_HOURS:
        print(f"[HoldTime] SELL blocked — only held {hours_held:.1f}h")
        return False
    return True

import grpc
from datetime import datetime, timedelta
from app.config import (ML_ENGINE_URL, MARKET_DATA_URL,
                        MIN_CONFIDENCE, USE_TESTNET)
from app.database import save_trade, get_avg_buy_price, get_last_buy_time
from app.binance_executor import (place_market_buy, place_market_sell,
                                   get_testnet_balance)
from app import ml_engine_pb2, ml_engine_pb2_grpc
from app import market_data_pb2, market_data_pb2_grpc

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

# ── STRATEGY PARAMETERS ───────────────────────────────────────────
STOP_LOSS_PCT      = 0.05   # 5% fixed stop loss
TRAILING_STOP_PCT  = 0.03   # 3% trailing stop loss
TAKE_PROFIT_1      = 0.10   # 10% → sell 30%
TAKE_PROFIT_2      = 0.15   # 15% → sell 50%
TAKE_PROFIT_3      = 0.20   # 20% → sell 100%
MIN_HOLD_HOURS     = 4
RSI_OVERBOUGHT     = 70
RSI_OVERSOLD       = 30
MAX_DAILY_LOSS_PCT = 0.10   # stop trading if -10% today
BASE_RISK_PCT      = 0.02   # base 2% risk per trade
MAX_RISK_PCT       = 0.20   # max 20% risk per trade

# gRPC channels
ML_GRPC_CHANNEL     = 'ml-decision-engine:50052'
MARKET_GRPC_CHANNEL = 'market-data-collector:50051'

# In-memory tracking
_highest_prices      = {}
_daily_start_balance = {}

def get_latest_price(symbol: str) -> float:
    channel = grpc.insecure_channel(MARKET_GRPC_CHANNEL)
    stub = market_data_pb2_grpc.MarketDataServiceStub(channel)
    request = market_data_pb2.PriceRequest(symbol=symbol.replace('/', '-'))
    response = stub.GetPrice(request, timeout=5)
    print(f"[gRPC] Price {symbol}: {response.price}")
    return float(response.price)

def get_latest_candle(symbol: str) -> dict:
    channel = grpc.insecure_channel(MARKET_GRPC_CHANNEL)
    stub = market_data_pb2_grpc.MarketDataServiceStub(channel)
    request = market_data_pb2.OHLCVRequest(
        symbol=symbol.replace('/', '-'),
        limit=100
    )
    response = stub.GetOHLCV(request, timeout=10)
    if not response.candles:
        return None
    latest = response.candles[-1]
    print(f"[gRPC] Got candle for {symbol}")
    return {
        'timestamp': latest.timestamp,
        'open': latest.open, 'high': latest.high,
        'low': latest.low, 'close': latest.close,
        'volume': latest.volume, 'rsi': latest.rsi,
        'ma20': latest.ma20, 'ma50': latest.ma50, 'ma200': latest.ma200,
        'returns': latest.returns, 'vol_20': latest.vol_20,
        'macd': latest.macd, 'macd_signal': latest.macd_signal,
        'macd_diff': latest.macd_diff,
        'bb_high': latest.bb_high, 'bb_low': latest.bb_low,
        'bb_mid': latest.bb_mid, 'bb_width': latest.bb_width,
        'bb_pct': latest.bb_pct, 'atr': latest.atr,
        'stoch_rsi': latest.stoch_rsi, 'stoch_rsi_k': latest.stoch_rsi_k,
        'stoch_rsi_d': latest.stoch_rsi_d,
        'volume_ratio': latest.volume_ratio,
        'dist_ma200': latest.dist_ma200, 'dist_ma50': latest.dist_ma50,
        'hour': latest.hour, 'day_of_week': latest.day_of_week,
        'close_lag_1': latest.close_lag_1, 'returns_lag_1': latest.returns_lag_1,
        'close_lag_2': latest.close_lag_2, 'returns_lag_2': latest.returns_lag_2,
        'close_lag_3': latest.close_lag_3, 'returns_lag_3': latest.returns_lag_3,
        'close_lag_6': latest.close_lag_6, 'returns_lag_6': latest.returns_lag_6,
        'close_lag_12': latest.close_lag_12, 'returns_lag_12': latest.returns_lag_12,
        'close_lag_24': latest.close_lag_24, 'returns_lag_24': latest.returns_lag_24,
    }

def get_ml_signal(symbol: str, candle: dict) -> dict:
    features = {}
    for col in FEATURE_COLS:
        if col in candle:
            features[col] = float(candle[col])
    if len(features) < 10:
        return None
    channel = grpc.insecure_channel(ML_GRPC_CHANNEL)
    stub = ml_engine_pb2_grpc.MLEngineServiceStub(channel)
    request = ml_engine_pb2.PredictRequest(
        symbol=symbol, features=features, publish=False
    )
    response = stub.Predict(request, timeout=10)
    print(f"[gRPC] Signal: {response.signal} ({response.confidence:.1f}%)")
    return {
        'signal': response.signal,
        'confidence': response.confidence,
        'model': response.model
    }

def kelly_criterion(confidence: float, win_rate: float = 0.55) -> float:
    """
    Kelly Criterion: f = (bp - q) / b
    Returns optimal fraction of capital to invest
    Half-Kelly used for safety
    """
    p = win_rate
    q = 1 - p
    b = confidence / 100
    kelly = (b * p - q) / b
    half_kelly = kelly / 2
    return max(0, min(half_kelly, MAX_RISK_PCT))

def calculate_volatility_factor(atr: float, price: float) -> float:
    """Reduce position size in high volatility markets"""
    if price <= 0 or atr <= 0:
        return 1.0
    atr_pct = atr / price
    if atr_pct > 0.05:
        return 0.5    # high volatility → half position
    elif atr_pct > 0.03:
        return 0.75   # medium volatility → 75% position
    else:
        return 1.0    # low volatility → full position

def check_max_daily_loss(symbol: str, current_balance: float) -> bool:
    """Stop trading if daily loss exceeds 10%"""
    today = datetime.utcnow().date().isoformat()
    key = f"{symbol}_{today}"
    if key not in _daily_start_balance:
        _daily_start_balance[key] = current_balance
        return False
    start = _daily_start_balance[key]
    if start <= 0:
        return False
    loss_pct = (start - current_balance) / start
    if loss_pct >= MAX_DAILY_LOSS_PCT:
        print(f"[RiskMgmt] Daily loss limit reached: {loss_pct*100:.1f}% — STOP TRADING")
        return True
    return False

def calculate_buy_size(
    usdt_balance: float,
    confidence: float,
    candle: dict = None
) -> float:
    """
    Sophisticated position sizing:
    1. Kelly Criterion — optimal bet size
    2. ATR volatility adjustment — reduce in volatile markets
    """
    if confidence < 50:
        return 0

    kelly_pct = kelly_criterion(confidence)

    atr   = candle.get('atr', 0)   if candle else 0
    price = candle.get('close', 1) if candle else 1
    vol_factor = calculate_volatility_factor(atr, price)

    position_pct  = kelly_pct * vol_factor
    position_pct  = max(BASE_RISK_PCT, min(position_pct, MAX_RISK_PCT))
    position_size = usdt_balance * position_pct

    print(f"[Strategy] Kelly={kelly_pct*100:.1f}% "
          f"VolFactor={vol_factor:.2f} "
          f"→ invest {position_pct*100:.1f}% = ${position_size:.2f}")

    return round(position_size, 2)

def calculate_sell_size(
    asset_balance: float,
    confidence: float,
    avg_buy_price: float,
    current_price: float,
    symbol: str = ""
) -> float:
    """
    Tiered take-profit strategy:
    +10% → sell 30%
    +15% → sell 50%
    +20% → sell 100%
    Loss  → sell 10%
    """
    if asset_balance <= 0:
        return 0

    pnl_pct = ((current_price - avg_buy_price) / avg_buy_price * 100) \
              if avg_buy_price > 0 else 0

    if pnl_pct >= TAKE_PROFIT_3 * 100:
        sell_pct = 1.0
        reason = f"Take Profit 3 (+{TAKE_PROFIT_3*100:.0f}%)"
    elif pnl_pct >= TAKE_PROFIT_2 * 100:
        sell_pct = 0.50
        reason = f"Take Profit 2 (+{TAKE_PROFIT_2*100:.0f}%)"
    elif pnl_pct >= TAKE_PROFIT_1 * 100:
        sell_pct = 0.30
        reason = f"Take Profit 1 (+{TAKE_PROFIT_1*100:.0f}%)"
    elif pnl_pct > 0:
        sell_pct = 0.25
        reason = "Small profit"
    else:
        sell_pct = 0.10
        reason = "Cut losses"

    sell_amount = asset_balance * sell_pct
    print(f"[Strategy] P&L={pnl_pct:.1f}% | {reason} "
          f"→ sell {sell_pct*100:.0f}% = {sell_amount:.6f}")
    return round(sell_amount, 6)

def check_stop_loss(
    avg_buy_price: float,
    current_price: float,
    symbol: str = ""
) -> bool:
    """
    Dual stop loss:
    1. Fixed stop loss: -5% from entry price
    2. Trailing stop loss: -3% from highest price
    """
    if avg_buy_price <= 0:
        return False

    # Update trailing stop tracker
    if symbol:
        if symbol not in _highest_prices:
            _highest_prices[symbol] = current_price
        elif current_price > _highest_prices[symbol]:
            _highest_prices[symbol] = current_price

    # Fixed stop loss
    drop_from_entry = (avg_buy_price - current_price) / avg_buy_price
    if drop_from_entry >= STOP_LOSS_PCT:
        print(f"[StopLoss] Fixed stop triggered! "
              f"drop={drop_from_entry*100:.1f}% from entry")
        return True

    # Trailing stop loss
    if symbol and symbol in _highest_prices:
        highest = _highest_prices[symbol]
        drop_from_high = (highest - current_price) / highest
        if drop_from_high >= TRAILING_STOP_PCT:
            print(f"[TrailingStop] Triggered! "
                  f"drop={drop_from_high*100:.1f}% from high ${highest:.2f}")
            if symbol in _highest_prices:
                del _highest_prices[symbol]
            return True

    return False

def check_trend_filter(candle: dict, signal: str) -> bool:
    """Multi-timeframe trend confirmation MA20/MA50/MA200"""
    ma20  = candle.get('ma20', 0)
    ma50  = candle.get('ma50', 0)
    ma200 = candle.get('ma200', 0)

    if signal == 'BUY':
        if ma20 < ma50:
            print(f"[TrendFilter] BUY blocked — MA20 < MA50 (downtrend)")
            return False
        return True

    if signal == 'SELL':
        if ma20 > ma50:
            print(f"[TrendFilter] SELL blocked — uptrend still active")
            return False
        return True

    return True

def check_rsi_filter(candle: dict, signal: str) -> bool:
    """RSI + StochRSI filter"""
    rsi       = candle.get('rsi', 50)
    stoch_rsi = candle.get('stoch_rsi', 0.5)

    if signal == 'BUY':
        if rsi > RSI_OVERBOUGHT:
            print(f"[RSIFilter] BUY blocked — overbought RSI={rsi:.1f}")
            return False
        if stoch_rsi > 0.8:
            print(f"[RSIFilter] BUY blocked — StochRSI overbought={stoch_rsi:.2f}")
            return False
    if signal == 'SELL':
        if rsi < RSI_OVERSOLD:
            print(f"[RSIFilter] SELL blocked — oversold RSI={rsi:.1f}")
            return False

    return True

def check_volume_filter(candle: dict, signal: str) -> bool:
    """Only trade when volume is above 80% of average"""
    volume_ratio = candle.get('volume_ratio', 1.0)
    if volume_ratio < 0.8:
        print(f"[VolumeFilter] {signal} blocked — low volume ratio={volume_ratio:.2f}")
        return False
    return True

def check_min_hold_time(symbol: str) -> bool:
    last_buy = get_last_buy_time(symbol)
    if not last_buy:
        return True
    hours_held = (datetime.utcnow() - last_buy).total_seconds() / 3600
    if hours_held < MIN_HOLD_HOURS:
        print(f"[HoldTime] SELL blocked — only held {hours_held:.1f}h")
        return False
    return True

def execute_trade(symbol: str) -> dict:
    asset = symbol.split('/')[0]

    try:
        usdt_balance  = get_testnet_balance('USDT')
        asset_balance = get_testnet_balance(asset)
        price         = get_latest_price(symbol)
        candle        = get_latest_candle(symbol)

        if not candle:
            return {"status": "error", "message": "Could not get market data"}

        if check_max_daily_loss(symbol, usdt_balance):
            return {"status": "blocked", "reason": "Daily loss limit reached"}

        signal_data = get_ml_signal(symbol, candle)
        if not signal_data:
            return {"status": "error", "message": "Could not get ML signal"}

        signal     = signal_data['signal']
        confidence = signal_data['confidence']
        model      = signal_data.get('model', 'Unknown')

        from app.database import save_signal
        save_signal({
            "symbol": symbol, "signal": signal,
            "confidence": confidence, "model": model,
            "price": price, "rsi": candle.get('rsi', 0),
            "source": "executor"
        })

        print(f"[Executor] {symbol} | {signal} ({confidence:.1f}%) | "
              f"USDT={usdt_balance:.2f} | {asset}={asset_balance:.6f}")

    except Exception as e:
        return {"status": "error", "message": str(e)}

    avg_buy_price = get_avg_buy_price(symbol)

    # Stop loss check (fixed + trailing)
    if asset_balance > 0.001 and check_stop_loss(avg_buy_price, price, symbol):
        sell_amount = asset_balance
        testnet_result = place_market_sell(symbol, sell_amount)
        if testnet_result['success']:
            save_trade({
                "symbol": symbol, "signal": "SELL",
                "confidence": 100.0, "price": testnet_result['price'],
                "quantity": testnet_result['quantity'],
                "capital_before": 0.0,
                "capital_after": sell_amount * testnet_result['price'],
                "position_value": 0.0,
                "trade_type": "STOP_LOSS", "status": "EXECUTED"
            })
            return {
                "status": "stop_loss_executed",
                "reason": "Stop-loss triggered",
                "price": testnet_result['price'],
                "usdt_after": get_testnet_balance('USDT')
            }

    if signal == "BUY" and usdt_balance > 10:
        if not check_trend_filter(candle, 'BUY'):
            return {"status": "filtered", "reason": "Downtrend — BUY blocked",
                    "signal": signal, "price": price}
        if not check_rsi_filter(candle, 'BUY'):
            return {"status": "filtered", "reason": "Overbought — BUY blocked",
                    "signal": signal, "price": price}
        if not check_volume_filter(candle, 'BUY'):
            return {"status": "filtered", "reason": "Low volume — BUY blocked",
                    "signal": signal, "price": price}

        invest_amount = calculate_buy_size(usdt_balance, confidence, candle)
        if invest_amount < 5:
            return {"status": "skipped", "reason": "Amount too small"}

        testnet_result = place_market_buy(symbol, invest_amount)
        if testnet_result['success']:
            _highest_prices[symbol] = price
            save_trade({
                "symbol": symbol, "signal": signal,
                "confidence": confidence,
                "price": testnet_result['price'],
                "quantity": testnet_result['quantity'],
                "capital_before": usdt_balance,
                "capital_after": usdt_balance - invest_amount,
                "position_value": testnet_result['quantity'] * testnet_result['price'],
                "trade_type": "TESTNET", "status": "EXECUTED"
            })
            return {
                "status": "executed", "signal": "BUY",
                "model": model, "invested": invest_amount,
                "quantity": testnet_result['quantity'],
                "price": testnet_result['price'],
                "usdt_after": get_testnet_balance('USDT'),
                f"{asset.lower()}_after": get_testnet_balance(asset)
            }
        else:
            return {"status": "error", "message": testnet_result['error']}

    elif signal == "SELL" and asset_balance > 0.001:
        if not check_min_hold_time(symbol):
            return {"status": "filtered",
                    "reason": "Min hold time not reached",
                    "signal": signal, "price": price}
        if not check_trend_filter(candle, 'SELL'):
            return {"status": "filtered", "reason": "Uptrend — SELL blocked",
                    "signal": signal, "price": price}
        if not check_rsi_filter(candle, 'SELL'):
            return {"status": "filtered", "reason": "Oversold — SELL blocked",
                    "signal": signal, "price": price}

        sell_amount = calculate_sell_size(
            asset_balance, confidence, avg_buy_price, price, symbol
        )
        if sell_amount < 0.0001:
            return {"status": "skipped", "reason": "Sell amount too small"}

        testnet_result = place_market_sell(symbol, sell_amount)
        if testnet_result['success']:
            save_trade({
                "symbol": symbol, "signal": signal,
                "confidence": confidence,
                "price": testnet_result['price'],
                "quantity": testnet_result['quantity'],
                "capital_before": 0.0,
                "capital_after": sell_amount * testnet_result['price'],
                "position_value": (asset_balance - sell_amount) * price,
                "trade_type": "TESTNET", "status": "EXECUTED"
            })
            return {
                "status": "executed", "signal": "SELL",
                "model": model, "sold": sell_amount,
                "price": testnet_result['price'],
                "usdt_after": get_testnet_balance('USDT'),
                f"{asset.lower()}_after": get_testnet_balance(asset)
            }
        else:
            return {"status": "error", "message": testnet_result['error']}

    else:
        return {
            "status": "hold", "signal": signal,
            "confidence": confidence, "model": model,
            "price": price, "usdt": usdt_balance,
            f"{asset.lower()}": asset_balance
        }