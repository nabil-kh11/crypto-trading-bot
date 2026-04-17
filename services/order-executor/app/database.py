import psycopg2
from psycopg2.extras import RealDictCursor
from app.config import DATABASE_URL

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id              SERIAL PRIMARY KEY,
            symbol          VARCHAR(20),
            signal          VARCHAR(10),
            confidence      FLOAT,
            price           FLOAT,
            quantity        FLOAT,
            capital_before  FLOAT,
            capital_after   FLOAT,
            position_value  FLOAT,
            trade_type      VARCHAR(10),
            status          VARCHAR(20),
            executed_at     TIMESTAMP DEFAULT NOW()
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id          SERIAL PRIMARY KEY,
            symbol      VARCHAR(20) UNIQUE,
            capital     FLOAT,
            position    FLOAT,
            avg_price   FLOAT,
            updated_at  TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()
    print("Database initialized — trades and portfolio tables ready")

def save_trade(trade: dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO trades
        (symbol, signal, confidence, price, quantity,
         capital_before, capital_after, position_value, trade_type, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        trade['symbol'], trade['signal'], trade['confidence'],
        trade['price'], trade['quantity'], trade['capital_before'],
        trade['capital_after'], trade['position_value'],
        trade['trade_type'], trade['status']
    ))
    conn.commit()
    cursor.close()
    conn.close()

def get_portfolio(symbol: str):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM portfolio WHERE symbol = %s", (symbol,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(result) if result else None

def update_portfolio(symbol: str, capital: float, position: float, avg_price: float):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO portfolio (symbol, capital, position, avg_price)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (symbol) DO UPDATE
        SET capital = %s, position = %s, avg_price = %s, updated_at = NOW()
    """, (symbol, capital, position, avg_price,
          capital, position, avg_price))
    conn.commit()
    cursor.close()
    conn.close()

def get_all_trades(symbol: str = None, limit: int = 50, offset: int = 0):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    if symbol:
        cursor.execute("""
            SELECT * FROM trades WHERE symbol = %s
            ORDER BY executed_at DESC LIMIT %s OFFSET %s
        """, (symbol, limit, offset))
    else:
        cursor.execute("""
            SELECT * FROM trades
            ORDER BY executed_at DESC LIMIT %s OFFSET %s
        """, (limit, offset))
    trades = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(t) for t in trades]
def get_trades_count(symbol: str = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    if symbol:
        cursor.execute("SELECT COUNT(*) FROM trades WHERE symbol = %s", (symbol,))
    else:
        cursor.execute("SELECT COUNT(*) FROM trades")
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count


def get_last_buy_time(symbol: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT executed_at FROM trades
        WHERE symbol = %s AND signal = 'BUY'
        ORDER BY executed_at DESC
        LIMIT 1
    """, (symbol,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None

def get_avg_buy_price(symbol: str) -> float:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT price FROM trades
        WHERE symbol = %s AND signal = 'BUY'
        ORDER BY executed_at DESC
        LIMIT 1
    """, (symbol,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return float(result[0]) if result and result[0] else 0.0

def init_signals_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id          SERIAL PRIMARY KEY,
            symbol      VARCHAR(20),
            signal      VARCHAR(10),
            confidence  FLOAT,
            model       VARCHAR(50),
            price       FLOAT,
            rsi         FLOAT,
            source      VARCHAR(20),
            created_at  TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def save_signal(signal: dict):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO signals
            (symbol, signal, confidence, model, price, rsi, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            signal.get('symbol'),
            signal.get('signal'),
            signal.get('confidence'),
            signal.get('model'),
            signal.get('price'),
            signal.get('rsi'),
            signal.get('source', 'executor')
        ))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error saving signal: {e}")
    finally:
        cursor.close()
        conn.close()

def get_signals(symbol: str = None, limit: int = 100):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    if symbol:
        cursor.execute("""
            SELECT * FROM signals WHERE symbol = %s
            ORDER BY created_at DESC LIMIT %s
        """, (symbol, limit))
    else:
        cursor.execute("""
            SELECT * FROM signals
            ORDER BY created_at DESC LIMIT %s
        """, (limit,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(r) for r in results]