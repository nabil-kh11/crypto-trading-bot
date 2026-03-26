import psycopg2
from psycopg2.extras import RealDictCursor
from app.config import DATABASE_URL

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sentiment_posts (
            id              SERIAL PRIMARY KEY,
            post_id         VARCHAR(20) UNIQUE NOT NULL,
            subreddit       VARCHAR(50),
            title           TEXT,
            body            TEXT,
            score           INTEGER,
            num_comments    INTEGER,
            created_utc     TIMESTAMP,
            sentiment_label VARCHAR(10),
            sentiment_score FLOAT,
            asset           VARCHAR(10),
            scraped_at      TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()
    print("Database initialized — sentiment_posts table ready")

def save_post(post: dict):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO sentiment_posts 
            (post_id, subreddit, title, body, score, num_comments, 
             created_utc, sentiment_label, sentiment_score, asset)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (post_id) DO NOTHING
        """, (
            post['post_id'], post['subreddit'], post['title'],
            post['body'], post['score'], post['num_comments'],
            post['created_utc'], post['sentiment_label'],
            post['sentiment_score'], post['asset']
        ))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error saving post: {e}")
    finally:
        cursor.close()
        conn.close()

def get_recent_posts(asset: str = None, limit: int = 100):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    if asset:
        cursor.execute("""
            SELECT * FROM sentiment_posts
            WHERE asset = %s
            ORDER BY created_utc DESC
            LIMIT %s
        """, (asset, limit))
    else:
        cursor.execute("""
            SELECT * FROM sentiment_posts
            ORDER BY created_utc DESC
            LIMIT %s
        """, (limit,))
    posts = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(p) for p in posts]

def get_sentiment_summary(asset: str):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT 
            asset,
            COUNT(*) as total_posts,
            AVG(sentiment_score) as avg_score,
            SUM(CASE WHEN sentiment_label = 'POSITIVE' THEN 1 ELSE 0 END) as positive,
            SUM(CASE WHEN sentiment_label = 'NEGATIVE' THEN 1 ELSE 0 END) as negative,
            SUM(CASE WHEN sentiment_label = 'NEUTRAL'  THEN 1 ELSE 0 END) as neutral
        FROM sentiment_posts
        WHERE asset = %s
        AND scraped_at > NOW() - INTERVAL '24 hours'
        GROUP BY asset
    """, (asset,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(result) if result else None