import grpc
from datetime import datetime
from app.config import (ML_ENGINE_URL, MARKET_DATA_URL,
                        MIN_CONFIDENCE, USE_TESTNET)
from app.database import save_trade, get_avg_buy_price, get_last_buy_time
from app.binance_executor import (place_market_buy, place_market_sell,
                                   get_testnet_balance)
from app import ml_engine_pb2, ml_engine_pb2_grpc
from app import market_data_pb2, market_data_pb2_grpc
from app.audit_logger import (
    log_signal_received, log_trade_filtered, log_trade_executed,
    log_stop_loss, log_daily_loss_limit, log_trade_error,
    log_strategy_change, log_hold
)

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

# ── STRATEGY DEFINITIONS ──────────────────────────────────────────
STRATEGIES = {
    'scalping': {
        'name': 'Scalping',
        'description': 'Short-term, frequent trades, small profits',
        'min_confidence':   35.0,
        'stop_loss':        0.02,
        'trailing_stop':    0.01,
        'take_profit_1':    0.02,
        'take_profit_2':    0.04,
        'take_profit_3':    0.06,
        'min_hold_hours':   0,
        'rsi_overbought':   80,
        'rsi_oversold':     20,
        'use_trend_filter': False,
        'use_stoch_filter': False,
        'use_volume_filter':False,
        'max_daily_loss':   0.05,
        'base_risk':        0.05,
        'max_risk':         0.15,
    },
    'swing': {
        'name': 'Swing Trading',
        'description': 'Medium-term, balanced risk/reward',
        'min_confidence':   50.0,
        'stop_loss':        0.05,
        'trailing_stop':    0.03,
        'take_profit_1':    0.10,
        'take_profit_2':    0.15,
        'take_profit_3':    0.20,
        'min_hold_hours':   4,
        'rsi_overbought':   70,
        'rsi_oversold':     30,
        'use_trend_filter': True,
        'use_stoch_filter': True,
        'use_volume_filter':True,
        'max_daily_loss':   0.10,
        'base_risk':        0.02,
        'max_risk':         0.20,
    },
    'position': {
        'name': 'Position Trading',
        'description': 'Long-term, high conviction trades',
        'min_confidence':   70.0,
        'stop_loss':        0.10,
        'trailing_stop':    0.05,
        'take_profit_1':    0.20,
        'take_profit_2':    0.30,
        'take_profit_3':    0.50,
        'min_hold_hours':   24,
        'rsi_overbought':   75,
        'rsi_oversold':     25,
        'use_trend_filter': True,
        'use_stoch_filter': True,
        'use_volume_filter':True,
        'max_daily_loss':   0.15,
        'base_risk':        0.10,
        'max_risk':         0.30,
    },
    'off': {
        'name': 'Off',
        'description': 'No trading — bot is disabled',
        'min_confidence':   100.0,
        'stop_loss':        0.05,
        'trailing_stop':    0.03,
        'take_profit_1':    0.10,
        'take_profit_2':    0.15,
        'take_profit_3':    0.20,
        'min_hold_hours':   999,
        'rsi_overbought':   70,
        'rsi_oversold':     30,
        'use_trend_filter': True,
        'use_stoch_filter': True,
        'use_volume_filter':True,
        'max_daily_loss':   0.0,
        'base_risk':        0.0,
        'max_risk':         0.0,
    }
}

_active_strategy = 'swing'

def get_strategy():
    return STRATEGIES[_active_strategy]

def set_strategy(name: str) -> bool:
    global _active_strategy
    if name in STRATEGIES:
        old = _active_strategy
        _active_strategy = name
        print(f"[Strategy] Switched to: {STRATEGIES[name]['name']}")
        log_strategy_change(old, name)   # ← AUDIT
        return True
    return False

def get_active_strategy_name() -> str:
    return _active_strategy

ML_GRPC_CHANNEL     = 'ml-decision-engine:50052'
MARKET_GRPC_CHANNEL = 'market-data-collector:50051'

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

def kelly_criterion(confidence: float, max_risk: float) -> float:
    p = 0.55
    q = 1 - p
    b = confidence / 100
    kelly = (b * p - q) / b
    half_kelly = kelly / 2
    return max(0, min(half_kelly, max_risk))

def calculate_volatility_factor(atr: float, price: float) -> float:
    if price <= 0 or atr <= 0:
        return 1.0
    atr_pct = atr / price
    if atr_pct > 0.05:
        return 0.5
    elif atr_pct > 0.03:
        return 0.75
    return 1.0

def check_max_daily_loss(symbol: str, total_portfolio: float) -> bool:
    s = get_strategy()
    today = datetime.utcnow().date().isoformat()
    key = f"{symbol}_{today}"
    if key not in _daily_start_balance:
        _daily_start_balance[key] = total_portfolio
        return False
    start = _daily_start_balance[key]
    if start <= 0:
        return False
    loss_pct = (start - total_portfolio) / start
    if loss_pct >= s['max_daily_loss']:
        print(f"[RiskMgmt] Daily loss limit: {loss_pct*100:.1f}% >= {s['max_daily_loss']*100:.0f}%")
        log_daily_loss_limit(symbol, loss_pct, s['max_daily_loss'], s['name'])  # ← AUDIT
        return True
    return False

def calculate_buy_size(usdt_balance: float, confidence: float, candle: dict = None) -> float:
    s = get_strategy()
    if confidence < s['min_confidence']:
        return 0
    kelly_pct = kelly_criterion(confidence, s['max_risk'])
    atr   = candle.get('atr', 0)   if candle else 0
    price = candle.get('close', 1) if candle else 1
    vol_factor = calculate_volatility_factor(atr, price)
    position_pct = kelly_pct * vol_factor
    position_pct = max(s['base_risk'], min(position_pct, s['max_risk']))
    position_size = usdt_balance * position_pct
    print(f"[{s['name']}] Kelly={kelly_pct*100:.1f}% VolFactor={vol_factor:.2f} "
          f"→ invest {position_pct*100:.1f}% = ${position_size:.2f}")
    return round(position_size, 2)

def calculate_sell_size(asset_balance: float, confidence: float,
                        avg_buy_price: float, current_price: float,
                        symbol: str = "") -> float:
    s = get_strategy()
    if asset_balance <= 0:
        return 0
    pnl_pct = ((current_price - avg_buy_price) / avg_buy_price * 100) \
              if avg_buy_price > 0 else 0
    if pnl_pct >= s['take_profit_3'] * 100:
        sell_pct = 1.0
        reason = f"Take Profit 3 (+{s['take_profit_3']*100:.0f}%)"
    elif pnl_pct >= s['take_profit_2'] * 100:
        sell_pct = 0.50
        reason = f"Take Profit 2 (+{s['take_profit_2']*100:.0f}%)"
    elif pnl_pct >= s['take_profit_1'] * 100:
        sell_pct = 0.30
        reason = f"Take Profit 1 (+{s['take_profit_1']*100:.0f}%)"
    elif pnl_pct > 0:
        sell_pct = 0.25
        reason = "Small profit"
    else:
        sell_pct = 0.10
        reason = "Cut losses"
    sell_amount = asset_balance * sell_pct
    print(f"[{s['name']}] P&L={pnl_pct:.1f}% | {reason} → sell {sell_pct*100:.0f}%")
    return round(sell_amount, 6)

def check_stop_loss(avg_buy_price: float, current_price: float, symbol: str = "") -> bool:
    s = get_strategy()
    if avg_buy_price <= 0:
        return False
    if symbol:
        if symbol not in _highest_prices:
            _highest_prices[symbol] = current_price
        elif current_price > _highest_prices[symbol]:
            _highest_prices[symbol] = current_price
    drop_from_entry = (avg_buy_price - current_price) / avg_buy_price
    if drop_from_entry >= s['stop_loss']:
        print(f"[StopLoss] Fixed stop triggered! drop={drop_from_entry*100:.1f}%")
        return True
    if symbol and symbol in _highest_prices:
        highest = _highest_prices[symbol]
        drop_from_high = (highest - current_price) / highest
        if drop_from_high >= s['trailing_stop']:
            print(f"[TrailingStop] Triggered! drop={drop_from_high*100:.1f}% from high")
            del _highest_prices[symbol]
            return True
    return False

def check_trend_filter(candle: dict, signal: str) -> bool:
    s = get_strategy()
    if not s['use_trend_filter']:
        return True
    ma20 = candle.get('ma20', 0)
    ma50 = candle.get('ma50', 0)
    if signal == 'BUY' and ma20 < ma50:
        print(f"[TrendFilter] BUY blocked — MA20 < MA50 (downtrend)")
        return False
    if signal == 'SELL' and ma20 > ma50:
        print(f"[TrendFilter] SELL blocked — uptrend still active")
        return False
    return True

def check_rsi_filter(candle: dict, signal: str) -> bool:
    s = get_strategy()
    rsi = candle.get('rsi', 50)
    stoch_rsi = candle.get('stoch_rsi', 0.5)
    if signal == 'BUY':
        if rsi > s['rsi_overbought']:
            print(f"[RSIFilter] BUY blocked — RSI={rsi:.1f}")
            return False
        if s['use_stoch_filter'] and stoch_rsi > 0.8:
            print(f"[RSIFilter] BUY blocked — StochRSI={stoch_rsi:.2f}")
            return False
    if signal == 'SELL':
        if rsi < s['rsi_oversold']:
            print(f"[RSIFilter] SELL blocked — RSI={rsi:.1f}")
            return False
    return True

def check_volume_filter(candle: dict, signal: str) -> bool:
    s = get_strategy()
    if not s['use_volume_filter']:
        return True
    volume_ratio = candle.get('volume_ratio', 1.0)
    if volume_ratio < 0.8:
        print(f"[VolumeFilter] {signal} blocked — volume_ratio={volume_ratio:.2f}")
        return False
    return True

def check_min_hold_time(symbol: str, pnl_pct: float = 0) -> bool:
    s = get_strategy()
    if pnl_pct > 0:
        return True
    if s['min_hold_hours'] == 0:
        return True
    last_buy = get_last_buy_time(symbol)
    if not last_buy:
        return True
    hours_held = (datetime.utcnow() - last_buy).total_seconds() / 3600
    if hours_held < s['min_hold_hours']:
        print(f"[HoldTime] SELL blocked — held {hours_held:.1f}h / {s['min_hold_hours']}h")
        return False
    return True

def execute_trade(symbol: str, signal: str, confidence: float, model: str) -> dict:
    s = get_strategy()

    if _active_strategy == 'off':
        return {"status": "disabled", "reason": "Trading is OFF"}

    asset = symbol.split('/')[0]

    try:
        usdt_balance  = get_testnet_balance('USDT')
        asset_balance = get_testnet_balance(asset)
        price         = get_latest_price(symbol)
        candle        = get_latest_candle(symbol)

        if not candle:
            return {"status": "error", "message": "Could not get market data"}

        btc_balance = get_testnet_balance('BTC')
        eth_balance = get_testnet_balance('ETH')
        if 'BTC' in symbol:
            btc_price = price
            eth_price = get_latest_price('ETH/USDT')
        else:
            btc_price = get_latest_price('BTC/USDT')
            eth_price = price
        total_portfolio = usdt_balance + (btc_balance * btc_price) + (eth_balance * eth_price)

        if check_max_daily_loss(symbol, total_portfolio):
            return {"status": "blocked", "reason": "Daily loss limit reached"}

        log_signal_received(symbol, signal, confidence, model, price, s['name'])

        if confidence < s['min_confidence'] and signal != 'HOLD':
            log_trade_filtered(symbol, signal,
                               f"Confidence {confidence:.1f}% < {s['min_confidence']}%",
                               price, s['name'], confidence)
            return {"status": "filtered",
                    "reason": f"Confidence {confidence:.1f}% < {s['min_confidence']}%",
                    "signal": signal, "price": price}

        from app.database import save_signal
        save_signal({
            "symbol": symbol, "signal": signal,
            "confidence": confidence, "model": model,
            "price": price, "rsi": candle.get('rsi', 0),
            "source": f"executor-{_active_strategy}"
        })

        print(f"[{s['name']}] {symbol} | {signal} ({confidence:.1f}%) | "
              f"USDT={usdt_balance:.2f} | {asset}={asset_balance:.6f} | "
              f"Portfolio=${total_portfolio:.2f}")

    except Exception as e:
        log_trade_error(symbol, str(e), s['name'])
        return {"status": "error", "message": str(e)}

    avg_buy_price = get_avg_buy_price(symbol)

    # ── Stop loss ─────────────────────────────────────────────────────────────
    if asset_balance > 0.001 and check_stop_loss(avg_buy_price, price, symbol):
        sell_amount = asset_balance
        loss_pct = (avg_buy_price - price) / avg_buy_price if avg_buy_price > 0 else 0
        log_stop_loss(symbol, price, avg_buy_price, sell_amount, loss_pct, s['name'])
        testnet_result = place_market_sell(symbol, sell_amount)
        if testnet_result['success']:
            save_trade({
                "symbol": symbol, "signal": "SELL",
                "confidence": 100.0, "price": testnet_result['price'],
                "quantity": testnet_result['quantity'],
                "capital_before": 0.0,
                "capital_after": sell_amount * testnet_result['price'],
                "position_value": 0.0,
                "trade_type": "STOP_LOSS", "status": "EXECUTED",
                "strategy": s['name']
            })
            log_trade_executed(symbol, "SELL", testnet_result['price'],
                               testnet_result['quantity'],
                               sell_amount * testnet_result['price'],
                               s['name'], 100.0, "STOP_LOSS")
            return {
                "status": "stop_loss_executed",
                "reason": "Stop-loss triggered",
                "strategy": s['name'],
                "price": testnet_result['price'],
                "usdt_after": get_testnet_balance('USDT')
            }

    # ── BUY ───────────────────────────────────────────────────────────────────
    if signal == "BUY" and usdt_balance > 10:
        if not check_trend_filter(candle, 'BUY'):
            log_trade_filtered(symbol, "BUY", "Downtrend — MA20 < MA50",
                               price, s['name'], confidence)
            return {"status": "filtered", "reason": "Downtrend — BUY blocked",
                    "signal": signal, "price": price}
        if not check_rsi_filter(candle, 'BUY'):
            log_trade_filtered(symbol, "BUY",
                               f"Overbought — RSI={candle.get('rsi',0):.1f}",
                               price, s['name'], confidence)
            return {"status": "filtered", "reason": "Overbought — BUY blocked",
                    "signal": signal, "price": price}
        if not check_volume_filter(candle, 'BUY'):
            log_trade_filtered(symbol, "BUY",
                               f"Low volume ratio={candle.get('volume_ratio',0):.2f}",
                               price, s['name'], confidence)
            return {"status": "filtered", "reason": "Low volume — BUY blocked",
                    "signal": signal, "price": price}

        invest_amount = calculate_buy_size(usdt_balance, confidence, candle)
        if invest_amount < 5:
            log_trade_filtered(symbol, "BUY", "Invest amount too small",
                               price, s['name'], confidence)
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
                "trade_type": "TESTNET", "status": "EXECUTED",
                "strategy": s['name']
            })
            log_trade_executed(symbol, "BUY", testnet_result['price'],
                               testnet_result['quantity'], invest_amount,
                               s['name'], confidence, "TESTNET", model)
            return {
                "status": "executed", "signal": "BUY",
                "strategy": s['name'],
                "model": model, "invested": invest_amount,
                "quantity": testnet_result['quantity'],
                "price": testnet_result['price'],
                "usdt_after": get_testnet_balance('USDT'),
                f"{asset.lower()}_after": get_testnet_balance(asset)
            }
        else:
            log_trade_error(symbol, testnet_result['error'], s['name'])
            return {"status": "error", "message": testnet_result['error']}

    # ── SELL ──────────────────────────────────────────────────────────────────
    elif signal == "SELL" and asset_balance > 0.001:
        pnl_pct = ((price - avg_buy_price) / avg_buy_price * 100) if avg_buy_price > 0 else 0

        if not check_min_hold_time(symbol, pnl_pct):
            log_trade_filtered(symbol, "SELL", "Min hold time not reached",
                               price, s['name'], confidence)
            return {"status": "filtered",
                    "reason": "Min hold time not reached",
                    "signal": signal, "price": price}
        if not check_trend_filter(candle, 'SELL'):
            log_trade_filtered(symbol, "SELL", "Uptrend still active — SELL blocked",
                               price, s['name'], confidence)
            return {"status": "filtered", "reason": "Uptrend — SELL blocked",
                    "signal": signal, "price": price}
        if not check_rsi_filter(candle, 'SELL'):
            log_trade_filtered(symbol, "SELL",
                               f"Oversold — RSI={candle.get('rsi',0):.1f}",
                               price, s['name'], confidence)
            return {"status": "filtered", "reason": "Oversold — SELL blocked",
                    "signal": signal, "price": price}

        sell_amount = calculate_sell_size(
            asset_balance, confidence, avg_buy_price, price, symbol
        )
        if sell_amount < 0.0001:
            log_trade_filtered(symbol, "SELL", "Sell amount too small",
                               price, s['name'], confidence)
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
                "trade_type": "TESTNET", "status": "EXECUTED",
                "strategy": s['name']
            })
            log_trade_executed(symbol, "SELL", testnet_result['price'],
                               testnet_result['quantity'],
                               sell_amount * testnet_result['price'],
                               s['name'], confidence, "TESTNET", model)
            return {
                "status": "executed", "signal": "SELL",
                "strategy": s['name'],
                "model": model, "sold": sell_amount,
                "price": testnet_result['price'],
                "usdt_after": get_testnet_balance('USDT'),
                f"{asset.lower()}_after": get_testnet_balance(asset)
            }
        else:
            log_trade_error(symbol, testnet_result['error'], s['name'])
            return {"status": "error", "message": testnet_result['error']}

    # ── HOLD ──────────────────────────────────────────────────────────────────
    else:
        log_hold(symbol, signal, confidence, price, s['name'])
        return {
            "status": "hold", "signal": signal,
            "strategy": s['name'],
            "confidence": confidence, "model": model,
            "price": price, "usdt": usdt_balance,
            f"{asset.lower()}": asset_balance
        }