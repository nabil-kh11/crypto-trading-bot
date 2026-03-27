import uvicorn
from fastapi import FastAPI
from app.database import init_db, get_all_trades, get_portfolio
from app.executor import execute_trade
from app.config import HOST, PORT

app = FastAPI(
    title="Order Executor",
    description="Paper trading execution service with capital management",
    version="1.0.0"
)

@app.on_event("startup")
def startup():
    init_db()
    print("Order Executor started!")

@app.get("/health")
def health():
    return {"status": "ok", "service": "order-executor"}

@app.post("/execute/{symbol}")
def execute(symbol: str):
    symbol = symbol.replace("-", "/").upper()
    return execute_trade(symbol)

@app.get("/trades")
def get_trades(symbol: str = None, limit: int = 50):
    return {"trades": get_all_trades(symbol=symbol, limit=limit)}

@app.get("/portfolio/{symbol}")
def portfolio(symbol: str):
    symbol = symbol.upper()
    data = get_portfolio(symbol)
    if not data:
        return {"message": f"No portfolio found for {symbol}"}
    return data

@app.get("/symbols")
def symbols():
    return {"symbols": ["BTC/USDT", "ETH/USDT"]}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)