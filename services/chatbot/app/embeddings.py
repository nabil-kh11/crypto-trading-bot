import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from app.config import EMBEDDING_MODEL, TOP_K_RESULTS
import psycopg2
from psycopg2.extras import RealDictCursor
from app.config import DATABASE_URL

model = SentenceTransformer(EMBEDDING_MODEL)

index = None
posts_cache = []

def build_index():
    global index, posts_cache
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

    if not posts:
        print("No posts found in database!")
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