"""
Audit Logger for Order Executor
Logs every trade decision to a structured audit log file (JSONL format).
Each line is a valid JSON object for easy parsing/analysis.
"""

import json
import logging
import os
from datetime import datetime, timezone

# ── Setup ─────────────────────────────────────────────────────────────────────
AUDIT_LOG_PATH = os.getenv("AUDIT_LOG_PATH", "/app/logs/audit.log")

# Ensure log directory exists
os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)

# File handler — one JSON object per line (JSONL)
_audit_logger = logging.getLogger("audit")
_audit_logger.setLevel(logging.INFO)
_audit_logger.propagate = False  # don't mix with app logs

if not _audit_logger.handlers:
    _fh = logging.FileHandler(AUDIT_LOG_PATH)
    _fh.setFormatter(logging.Formatter("%(message)s"))
    _audit_logger.addHandler(_fh)

    # Also print to stdout so it shows in docker logs
    _sh = logging.StreamHandler()
    _sh.setFormatter(logging.Formatter("[AUDIT] %(message)s"))
    _audit_logger.addHandler(_sh)


# ── Core writer ───────────────────────────────────────────────────────────────
def _write(event_type: str, data: dict):
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event":     event_type,
        **data
    }
    _audit_logger.info(json.dumps(record))


# ── Public API ────────────────────────────────────────────────────────────────
def log_signal_received(symbol: str, signal: str, confidence: float,
                        model: str, price: float, strategy: str):
    """Log every ML signal received before any filtering."""
    _write("SIGNAL_RECEIVED", {
        "symbol":     symbol,
        "signal":     signal,
        "confidence": round(confidence, 2),
        "model":      model,
        "price":      price,
        "strategy":   strategy,
    })


def log_trade_filtered(symbol: str, signal: str, reason: str,
                       price: float, strategy: str, confidence: float = 0):
    """Log when a trade is blocked by any filter."""
    _write("TRADE_FILTERED", {
        "symbol":     symbol,
        "signal":     signal,
        "reason":     reason,
        "price":      price,
        "strategy":   strategy,
        "confidence": round(confidence, 2),
    })


def log_trade_executed(symbol: str, signal: str, price: float,
                       quantity: float, invested_usdt: float,
                       strategy: str, confidence: float,
                       trade_type: str, model: str = ""):
    """Log every successfully executed trade."""
    _write("TRADE_EXECUTED", {
        "symbol":        symbol,
        "signal":        signal,
        "price":         price,
        "quantity":      quantity,
        "invested_usdt": round(invested_usdt, 2),
        "strategy":      strategy,
        "confidence":    round(confidence, 2),
        "trade_type":    trade_type,
        "model":         model,
    })


def log_stop_loss(symbol: str, price: float, avg_buy_price: float,
                  quantity: float, loss_pct: float, strategy: str):
    """Log stop-loss / trailing-stop triggers."""
    _write("STOP_LOSS_TRIGGERED", {
        "symbol":        symbol,
        "price":         price,
        "avg_buy_price": avg_buy_price,
        "quantity":      quantity,
        "loss_pct":      round(loss_pct, 4),
        "strategy":      strategy,
    })


def log_daily_loss_limit(symbol: str, loss_pct: float,
                         limit_pct: float, strategy: str):
    """Log when daily loss limit blocks all trading."""
    _write("DAILY_LOSS_LIMIT_HIT", {
        "symbol":    symbol,
        "loss_pct":  round(loss_pct, 4),
        "limit_pct": round(limit_pct, 4),
        "strategy":  strategy,
    })


def log_trade_error(symbol: str, error: str, strategy: str):
    """Log unexpected errors during trade execution."""
    _write("TRADE_ERROR", {
        "symbol":   symbol,
        "error":    error,
        "strategy": strategy,
    })


def log_strategy_change(old_strategy: str, new_strategy: str):
    """Log every strategy switch from the dashboard."""
    _write("STRATEGY_CHANGED", {
        "from": old_strategy,
        "to":   new_strategy,
    })


def log_hold(symbol: str, signal: str, confidence: float,
             price: float, strategy: str):
    """Log HOLD decisions (signal not actionable)."""
    _write("HOLD", {
        "symbol":     symbol,
        "signal":     signal,
        "confidence": round(confidence, 2),
        "price":      price,
        "strategy":   strategy,
    })
