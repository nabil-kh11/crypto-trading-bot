import requests
from datetime import datetime, timedelta
from app.config import (ML_ENGINE_URL, MARKET_DATA_URL,
                        MIN_CONFIDENCE, USE_TESTNET)
from app.database import save_trade, get_avg_buy_price, get_last_buy_time
from app.binance_executor import (place_market_buy, place_market_sell,
                                   get_testnet_balance)

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

STOP_LOSS_PCT    = 0.05   # Force sell if price drops 5% from avg buy
MIN_HOLD_HOURS   = 4      # Don't sell within 4 hours of buying
RSI_OVERBOUGHT   = 70     # Don't buy if RSI above this
RSI_OVERSOLD     = 30     # Don't sell if RSI below this

def get_latest_price(symbol: str) -> float:
    symbol_url = symbol.replace("/", "-")
    response = requests.get(f"{MARKET_DATA_URL}/price/{symbol_url}", timeout=5)
    return float(response.json()["price"])

def get_latest_candle(symbol: str) -> dict:
    """Get latest candle with all indicators"""
    symbol_url = symbol.replace("/", "-")
    response = requests.get(
        f"{MARKET_DATA_URL}/ohlcv/{symbol_url}?limit=100", timeout=10)
    candles = response.json()
    if not candles:
        return None
    return candles[-1]

def get_ml_signal(symbol: str, candle: dict) -> dict:
    try:
        features = {}
        for col in FEATURE_COLS:
            if col in candle:
                features[col] = candle[col]
            else:
                return None
        response = requests.post(
            f"{ML_ENGINE_URL}/predict?publish=false", json={
                "symbol": symbol,
                "features": features
            }, timeout=10)
        if response.status_code != 200:
            return None
        return response.json()
    except Exception as e:
        print(f"Error getting ML signal: {e}")
        return None

def calculate_buy_size(usdt_balance: float, confidence: float) -> float:
    """
    Confidence controls position size — never skips signal completely
    Range: 1% to 20% of capital based on confidence
    """
    min_pct = 0.01   # 1% minimum always
    max_pct = 0.20   # 20% maximum
    position_pct = min_pct + (confidence / 100) * (max_pct - min_pct)
    position_size = usdt_balance * position_pct
    print(f"[Strategy] Confidence {confidence:.1f}% → invest {position_pct*100:.1f}% = ${position_size:.2f}")
    return round(position_size, 2)

def calculate_sell_size(asset_balance: float, confidence: float,
                        avg_buy_price: float, current_price: float) -> float:
    """
    Sell size based on profit level — always sells something on SELL signal
    """
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
        sell_pct = 0.10  # Always sell at least 10% on SELL signal

    sell_amount = asset_balance * sell_pct
    print(f"[Strategy] P&L={pnl_pct:.1f}% → sell {sell_pct*100:.0f}% = {sell_amount:.6f}")
    return round(sell_amount, 6)

def check_stop_loss(avg_buy_price: float, current_price: float) -> bool:
    """Returns True if stop-loss triggered"""
    if avg_buy_price <= 0:
        return False
    drop_pct = (avg_buy_price - current_price) / avg_buy_price
    if drop_pct >= STOP_LOSS_PCT:
        print(f"[StopLoss] Triggered! avg_buy={avg_buy_price} current={current_price} drop={drop_pct*100:.1f}%")
        return True
    return False

def check_trend_filter(candle: dict, signal: str) -> bool:
    """
    Trend confirmation filter:
    BUY only in uptrend (MA20 > MA50)
    SELL only in downtrend (MA20 < MA50)
    """
    ma20 = candle.get('ma20', 0)
    ma50 = candle.get('ma50', 0)

    if signal == 'BUY' and ma20 < ma50:
        print(f"[TrendFilter] BUY blocked — downtrend (MA20={ma20:.0f} < MA50={ma50:.0f})")
        return False
    if signal == 'SELL' and ma20 > ma50:
        print(f"[TrendFilter] SELL blocked — uptrend (MA20={ma20:.0f} > MA50={ma50:.0f})")
        return False
    return True




def check_rsi_filter(candle: dict, signal: str) -> bool:
    """
    RSI filter:
    Don't BUY if overbought (RSI > 70)
    Don't SELL if oversold (RSI < 30)
    """
    rsi = candle.get('rsi', 50)

    if signal == 'BUY' and rsi > RSI_OVERBOUGHT:
        print(f"[RSIFilter] BUY blocked — overbought (RSI={rsi:.1f} > {RSI_OVERBOUGHT})")
        return False
    if signal == 'SELL' and rsi < RSI_OVERSOLD:
        print(f"[RSIFilter] SELL blocked — oversold (RSI={rsi:.1f} < {RSI_OVERSOLD})")
        return False
    return True

def check_min_hold_time(symbol: str) -> bool:
    """Returns True if enough time has passed since last buy"""
    last_buy = get_last_buy_time(symbol)
    if not last_buy:
        return True
    hours_held = (datetime.utcnow() - last_buy).total_seconds() / 3600
    if hours_held < MIN_HOLD_HOURS:
        print(f"[HoldTime] SELL blocked — only held {hours_held:.1f}h (min {MIN_HOLD_HOURS}h)")
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

        # Log signal
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

    # ── STOP-LOSS (overrides everything) ─────────────────
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

    # ── BUY ──────────────────────────────────────────────
    if signal == "BUY" and usdt_balance > 10:

        if not check_trend_filter(candle, 'BUY'):
            return {"status": "filtered", "reason": "Downtrend — BUY blocked",
                    "signal": signal, "price": price}

        if not check_rsi_filter(candle, 'BUY'):
            return {"status": "filtered", "reason": "Overbought — BUY blocked",
                    "signal": signal, "price": price}

        # Confidence controls size — never skips
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

    # ── SELL ─────────────────────────────────────────────
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

    # ── HOLD ─────────────────────────────────────────────
    else:
        return {
            "status": "hold", "signal": signal,
            "confidence": confidence, "model": model,
            "price": price, "usdt": usdt_balance,
            f"{asset.lower()}": asset_balance
        }
    asset = symbol.split('/')[0]

    try:
        # Get real balances from Binance testnet
        usdt_balance  = get_testnet_balance('USDT')
        asset_balance = get_testnet_balance(asset)
        price         = get_latest_price(symbol)

        # Get latest candle with indicators
        candle = get_latest_candle(symbol)
        if not candle:
            return {"status": "error", "message": "Could not get market data"}

        # Get ML signal
        signal_data = get_ml_signal(symbol, candle)
        if not signal_data:
            return {"status": "error", "message": "Could not get ML signal"}

        signal     = signal_data['signal']
        confidence = signal_data['confidence']
        model      = signal_data.get('model', 'Unknown')

        print(f"[Executor] {symbol} | Signal={signal} ({confidence:.1f}%) | "
              f"USDT={usdt_balance:.2f} | {asset}={asset_balance:.6f} | Price={price}")

    except Exception as e:
        return {"status": "error", "message": str(e)}

    # ── GET CONTEXT ──────────────────────────────────────────
    avg_buy_price = get_avg_buy_price(symbol)

    # ── STOP-LOSS CHECK (overrides everything) ────────────────
    if asset_balance > 0.001 and check_stop_loss(avg_buy_price, price):
        sell_amount   = asset_balance  # Sell everything on stop-loss
        testnet_result = place_market_sell(symbol, sell_amount)
        if testnet_result['success']:
            save_trade({
                "symbol":         symbol,
                "signal":         "SELL",
                "confidence":     100.0,
                "price":          testnet_result['price'],
                "quantity":       testnet_result['quantity'],
                "capital_before": 0.0,
                "capital_after":  sell_amount * testnet_result['price'],
                "position_value": 0.0,
                "trade_type":     "STOP_LOSS",
                "status":         "EXECUTED"
            })
            return {
                "status":    "stop_loss_executed",
                "signal":    "SELL",
                "reason":    "Stop-loss triggered (-5%)",
                "price":     testnet_result['price'],
                "quantity":  testnet_result['quantity'],
                "usdt_after": get_testnet_balance('USDT')
            }

    # ── CONFIDENCE CHECK ──────────────────────────────────────
    if confidence < MIN_CONFIDENCE:
        return {
            "status":     "skipped",
            "reason":     f"Low confidence {confidence:.1f}% < {MIN_CONFIDENCE}%",
            "signal":     signal,
            "model":      model,
            "price":      price
        }

    # ── BUY LOGIC ─────────────────────────────────────────────
    if signal == "BUY" and usdt_balance > 10:

        # Trend filter
        if not check_trend_filter(candle, 'BUY'):
            return {"status": "filtered", "reason": "Downtrend — BUY blocked",
                    "signal": signal, "price": price}

        # RSI filter
        if not check_rsi_filter(candle, 'BUY'):
            return {"status": "filtered", "reason": "Overbought — BUY blocked",
                    "signal": signal, "rsi": candle.get('rsi'), "price": price}

        invest_amount = calculate_buy_size(usdt_balance, confidence)
        if invest_amount < 10:
            return {"status": "skipped", "reason": f"Position too small: ${invest_amount}"}

        testnet_result = place_market_buy(symbol, invest_amount)
        if testnet_result['success']:
            save_trade({
                "symbol":         symbol,
                "signal":         signal,
                "confidence":     confidence,
                "price":          testnet_result['price'],
                "quantity":       testnet_result['quantity'],
                "capital_before": usdt_balance,
                "capital_after":  usdt_balance - invest_amount,
                "position_value": testnet_result['quantity'] * testnet_result['price'],
                "trade_type":     "TESTNET",
                "status":         "EXECUTED"
            })
            return {
                "status":     "executed",
                "signal":     "BUY",
                "model":      model,
                "invested":   invest_amount,
                "quantity":   testnet_result['quantity'],
                "price":      testnet_result['price'],
                "usdt_after": get_testnet_balance('USDT'),
                f"{asset.lower()}_after": get_testnet_balance(asset)
            }
        else:
            return {"status": "error", "message": testnet_result['error']}

    # ── SELL LOGIC ────────────────────────────────────────────
    elif signal == "SELL" and asset_balance > 0.001:

        # Minimum hold time check
        if not check_min_hold_time(symbol):
            return {"status": "filtered",
                    "reason": f"Min hold time not reached ({MIN_HOLD_HOURS}h)",
                    "signal": signal, "price": price}

        # Trend filter
        if not check_trend_filter(candle, 'SELL'):
            return {"status": "filtered", "reason": "Uptrend — SELL blocked",
                    "signal": signal, "price": price}

        # RSI filter
        if not check_rsi_filter(candle, 'SELL'):
            return {"status": "filtered", "reason": "Oversold — SELL blocked",
                    "signal": signal, "rsi": candle.get('rsi'), "price": price}

        sell_amount = calculate_sell_size(asset_balance, confidence,
                                          avg_buy_price, price)
        if sell_amount < 0.0001:
            return {"status": "skipped", "reason": "Sell amount too small"}

        testnet_result = place_market_sell(symbol, sell_amount)
        if testnet_result['success']:
            save_trade({
                "symbol":         symbol,
                "signal":         signal,
                "confidence":     confidence,
                "price":          testnet_result['price'],
                "quantity":       testnet_result['quantity'],
                "capital_before": 0.0,
                "capital_after":  sell_amount * testnet_result['price'],
                "position_value": (asset_balance - sell_amount) * price,
                "trade_type":     "TESTNET",
                "status":         "EXECUTED"
            })
            return {
                "status":     "executed",
                "signal":     "SELL",
                "model":      model,
                "sold":       sell_amount,
                "price":      testnet_result['price'],
                "usdt_after": get_testnet_balance('USDT'),
                f"{asset.lower()}_after": get_testnet_balance(asset)
            }
        else:
            return {"status": "error", "message": testnet_result['error']}

    # ── HOLD ──────────────────────────────────────────────────
    else:
        return {
            "status":     "hold",
            "signal":     signal,
            "confidence": confidence,
            "model":      model,
            "price":      price,
            "usdt":       usdt_balance,
            f"{asset.lower()}": asset_balance
        }