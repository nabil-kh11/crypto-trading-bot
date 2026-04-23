import os
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from app.config import EMBEDDING_MODEL, TOP_K_RESULTS, DATABASE_URL
import psycopg2
from psycopg2.extras import RealDictCursor

model = SentenceTransformer(EMBEDDING_MODEL)
index = None
posts_cache = []

# Paths for pre-built index
INDEX_PATH = "/app/data/faiss.index"
POSTS_PATH = "/app/data/posts.pkl"


def load_prebuilt_index():
    """Load pre-built FAISS index from disk (instant startup)."""
    global index, posts_cache
    if os.path.exists(INDEX_PATH) and os.path.exists(POSTS_PATH):
        print("Loading pre-built FAISS index from disk...")
        index = faiss.read_index(INDEX_PATH)
        with open(POSTS_PATH, 'rb') as f:
            posts_cache = pickle.load(f)
        print(f"Loaded FAISS index with {index.ntotal} vectors instantly!")
        return True
    return False


def build_index():
    """Build FAISS index — tries pre-built first, then DB, then in-memory."""
    global index, posts_cache

    # Try loading pre-built index first (instant)
    if load_prebuilt_index():
        return len(posts_cache)

    # Fall back to building from DB
    print("No pre-built index found, building from database...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT id, title, body, asset, sentiment_label,
                   sentiment_score, subreddit, created_utc
            FROM sentiment_posts
            ORDER BY created_utc DESC
            LIMIT 1000
        """)
        posts = [dict(p) for p in cursor.fetchall()]
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"DB error: {e} — using empty index")
        posts = []

    if not posts:
        print("No posts found — FAISS index will be empty")
        index = faiss.IndexFlatL2(384)
        posts_cache = []
        return 0

    texts = [f"{p['title']} {p['body']}" for p in posts]
    embeddings = model.encode(texts, show_progress_bar=True)
    embeddings = np.array(embeddings).astype('float32')
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    posts_cache = posts
    print(f"Built FAISS index with {len(posts)} posts!")
    return len(posts)


def search_similar(query: str, k: int = TOP_K_RESULTS):
    global index, posts_cache
    if index is None:
        build_index()
    if index is None or len(posts_cache) == 0:
        return []
    query_embedding = model.encode([query]).astype('float32')
    distances, indices = index.search(query_embedding, k)
    results = []
    for idx in indices[0]:
        if idx < len(posts_cache):
            results.append(posts_cache[idx])
    return results