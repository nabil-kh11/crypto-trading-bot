import ccxt
import os
from dotenv import load_dotenv


# Load .env from project root
load_dotenv('/app/.env')


BINANCE_TESTNET_API_KEY    = os.getenv("BINANCE_TESTNET_API_KEY", "")
BINANCE_TESTNET_SECRET_KEY = os.getenv("BINANCE_TESTNET_SECRET_KEY", "")
USE_TESTNET                = os.getenv("USE_TESTNET", "true").lower() == "true"

def get_exchange():
    exchange = ccxt.binance({
        'apiKey': BINANCE_TESTNET_API_KEY,
        'secret': BINANCE_TESTNET_SECRET_KEY,
        'options': {
            'defaultType': 'spot',
        }
    })
    if USE_TESTNET:
        exchange.set_sandbox_mode(True)
    return exchange

def get_testnet_balance(asset: str = 'USDT') -> float:
    try:
        exchange = get_exchange()
        balance = exchange.fetch_balance()
        return float(balance['free'].get(asset, 0))
    except Exception as e:
        print(f"Error fetching testnet balance: {e}")
        return 0.0

def place_market_buy(symbol: str, usdt_amount: float) -> dict:
    try:
        exchange = get_exchange()
        ticker = exchange.fetch_ticker(symbol)
        price = ticker['last']
        quantity = usdt_amount / price
        market = exchange.market(symbol)
        quantity = exchange.amount_to_precision(symbol, quantity)
        order = exchange.create_market_buy_order(symbol, quantity)
        print(f"[Testnet] BUY order placed: {quantity} {symbol} at ~${price}")
        return {
            "success":  True,
            "order_id": order['id'],
            "symbol":   symbol,
            "quantity": float(quantity),
            "price":    price,
            "status":   order['status']
        }
    except Exception as e:
        print(f"[Testnet] BUY order failed: {e}")
        return {"success": False, "error": str(e)}

def place_market_sell(symbol: str, quantity: float) -> dict:
    try:
        exchange = get_exchange()
        quantity = exchange.amount_to_precision(symbol, quantity)
        order = exchange.create_market_sell_order(symbol, quantity)
        ticker = exchange.fetch_ticker(symbol)
        price = ticker['last']
        print(f"[Testnet] SELL order placed: {quantity} {symbol} at ~${price}")
        return {
            "success":  True,
            "order_id": order['id'],
            "symbol":   symbol,
            "quantity": float(quantity),
            "price":    price,
            "status":   order['status']
        }
    except Exception as e:
        print(f"[Testnet] SELL order failed: {e}")
        return {"success": False, "error": str(e)}

def get_testnet_orders(symbol: str) -> list:
    try:
        exchange = get_exchange()
        orders = exchange.fetch_orders(symbol, limit=10)
        return orders
    except Exception as e:
        print(f"Error fetching testnet orders: {e}")
        return []
    
def get_exchange():
    exchange = ccxt.binance({
        'apiKey': BINANCE_TESTNET_API_KEY,
        'secret': BINANCE_TESTNET_SECRET_KEY,
        'options': {
            'defaultType': 'spot',
        }
    })
    if USE_TESTNET:
        exchange.set_sandbox_mode(True)
    exchange.load_markets()
    return exchange