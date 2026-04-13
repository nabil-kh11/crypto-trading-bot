import requests
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

STOP_LOSS_PCT  = 0.05
MIN_HOLD_HOURS = 4
RSI_OVERBOUGHT = 70
RSI_OVERSOLD   = 30

# gRPC channels
ML_GRPC_CHANNEL     = 'ml-decision-engine:50052'
MARKET_GRPC_CHANNEL = 'market-data-collector:50051'

def get_latest_price(symbol: str) -> float:
    """Get price via gRPC"""
    channel = grpc.insecure_channel(MARKET_GRPC_CHANNEL)
    stub = market_data_pb2_grpc.MarketDataServiceStub(channel)
    request = market_data_pb2.PriceRequest(symbol=symbol.replace('/', '-'))
    response = stub.GetPrice(request, timeout=5)
    print(f"[gRPC] Price {symbol}: {response.price}")
    return float(response.price)

def get_latest_candle(symbol: str) -> dict:
    """Get latest candle via gRPC"""
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
        'open': latest.open,
        'high': latest.high,
        'low': latest.low,
        'close': latest.close,
        'volume': latest.volume,
        'rsi': latest.rsi,
        'ma20': latest.ma20,
        'ma50': latest.ma50,
        'ma200': latest.ma200,
        'returns': latest.returns,
        'vol_20': latest.vol_20,
        'macd': latest.macd,
        'macd_signal': latest.macd_signal,
        'macd_diff': latest.macd_diff,
        'bb_high': latest.bb_high,
        'bb_low': latest.bb_low,
        'bb_mid': latest.bb_mid,
        'bb_width': latest.bb_width,
        'bb_pct': latest.bb_pct,
        'atr': latest.atr,
        'stoch_rsi': latest.stoch_rsi,
        'stoch_rsi_k': latest.stoch_rsi_k,
        'stoch_rsi_d': latest.stoch_rsi_d,
        'volume_ratio': latest.volume_ratio,
        'dist_ma200': latest.dist_ma200,
        'dist_ma50': latest.dist_ma50,
        'hour': latest.hour,
        'day_of_week': latest.day_of_week,
        'close_lag_1': latest.close_lag_1,
        'returns_lag_1': latest.returns_lag_1,
        'close_lag_2': latest.close_lag_2,
        'returns_lag_2': latest.returns_lag_2,
        'close_lag_3': latest.close_lag_3,
        'returns_lag_3': latest.returns_lag_3,
        'close_lag_6': latest.close_lag_6,
        'returns_lag_6': latest.returns_lag_6,
        'close_lag_12': latest.close_lag_12,
        'returns_lag_12': latest.returns_lag_12,
        'close_lag_24': latest.close_lag_24,
        'returns_lag_24': latest.returns_lag_24,
    }
    """Get latest candle via gRPC"""
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
        'open': latest.open,
        'high': latest.high,
        'low': latest.low,
        'close': latest.close,
        'volume': latest.volume,
        'rsi': latest.rsi,
        'ma20': latest.ma20,
        'ma50': latest.ma50,
    }
def get_ml_signal(symbol: str, candle: dict) -> dict:
    """Get ML signal via gRPC"""
    features = {}
    for col in FEATURE_COLS:
        if col in candle:
            features[col] = float(candle[col])

    if len(features) < 10:
        return None

    channel = grpc.insecure_channel(ML_GRPC_CHANNEL)
    stub = ml_engine_pb2_grpc.MLEngineServiceStub(channel)
    request = ml_engine_pb2.PredictRequest(
        symbol=symbol,
        features=features,
        publish=False
    )
    response = stub.Predict(request, timeout=10)
    print(f"[gRPC] Signal: {response.signal} ({response.confidence:.1f}%)")
    return {
        'signal': response.signal,
        'confidence': response.confidence,
        'model': response.model
    }

def calculate_buy_size(usdt_balance: float, confidence: float) -> float:
    if confidence <= MIN_CONFIDENCE:
        return 0
    if confidence < 50:
        return 0
    confidence_factor = (confidence - 50) / 50
    base_risk = 0.02
    max_risk  = 0.20
    position_pct  = base_risk + confidence_factor * (max_risk - base_risk)
    position_size = usdt_balance * position_pct
    print(f"[Strategy] Confidence {confidence:.1f}% → invest {position_pct*100:.1f}% = ${position_size:.2f}")
    return round(position_size, 2)

def calculate_sell_size(asset_balance: float, confidence: float,
                        avg_buy_price: float, current_price: float) -> float:
    if asset_balance <= 0:
        return 0
    pnl_pct = ((current_price - avg_buy_price) / avg_buy_price * 100) if avg_buy_price > 0 else 0
    if pnl_pct > 20 and confidence > 70:
        sell_pct = 1.0
    elif pnl_pct > 10:
        sell_pct = 0.75
    elif pnl_pct > 5:
        sell_pct = 0.50
    elif pnl_pct > 0:
        sell_pct = 0.25
    else:
        sell_pct = 0.10
    sell_amount = asset_balance * sell_pct
    print(f"[Strategy] P&L={pnl_pct:.1f}% → sell {sell_pct*100:.0f}% = {sell_amount:.6f}")
    return round(sell_amount, 6)

def check_stop_loss(avg_buy_price: float, current_price: float) -> bool:
    if avg_buy_price <= 0:
        return False
    drop_pct = (avg_buy_price - current_price) / avg_buy_price
    if drop_pct >= STOP_LOSS_PCT:
        print(f"[StopLoss] Triggered! drop={drop_pct*100:.1f}%")
        return True
    return False

def check_trend_filter(candle: dict, signal: str) -> bool:
    ma20 = candle.get('ma20', 0)
    ma50 = candle.get('ma50', 0)
    if signal == 'BUY' and ma20 < ma50:
        print(f"[TrendFilter] BUY blocked — downtrend")
        return False
    if signal == 'SELL' and ma20 > ma50:
        print(f"[TrendFilter] SELL blocked — uptrend")
        return False
    return True

def check_rsi_filter(candle: dict, signal: str) -> bool:
    rsi = candle.get('rsi', 50)
    if signal == 'BUY' and rsi > RSI_OVERBOUGHT:
        print(f"[RSIFilter] BUY blocked — overbought RSI={rsi:.1f}")
        return False
    if signal == 'SELL' and rsi < RSI_OVERSOLD:
        print(f"[RSIFilter] SELL blocked — oversold RSI={rsi:.1f}")
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

    if asset_balance > 0.001 and check_stop_loss(avg_buy_price, price):
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
                "reason": "Stop-loss triggered (-5%)",
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

        invest_amount = calculate_buy_size(usdt_balance, confidence)
        if invest_amount < 5:
            return {"status": "skipped", "reason": "Amount too small"}

        testnet_result = place_market_buy(symbol, invest_amount)
        if testnet_result['success']:
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
                    "reason": f"Min hold time not reached",
                    "signal": signal, "price": price}
        if not check_trend_filter(candle, 'SELL'):
            return {"status": "filtered", "reason": "Uptrend — SELL blocked",
                    "signal": signal, "price": price}
        if not check_rsi_filter(candle, 'SELL'):
            return {"status": "filtered", "reason": "Oversold — SELL blocked",
                    "signal": signal, "price": price}

        sell_amount = calculate_sell_size(asset_balance, confidence,
                                          avg_buy_price, price)
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