from groq import Groq
from app.config import GROQ_API_KEY, TOP_K_RESULTS
from app.embeddings import search_similar
import psycopg2
from psycopg2.extras import RealDictCursor
from app.config import DATABASE_URL

client = Groq(api_key=GROQ_API_KEY)

def get_sentiment_summary(asset: str) -> dict:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT
            asset,
            COUNT(*) as total,
            ROUND(AVG(sentiment_score)::numeric, 3) as avg_score,
            SUM(CASE WHEN sentiment_label='POSITIVE' THEN 1 ELSE 0 END) as positive,
            SUM(CASE WHEN sentiment_label='NEGATIVE' THEN 1 ELSE 0 END) as negative,
            SUM(CASE WHEN sentiment_label='NEUTRAL'  THEN 1 ELSE 0 END) as neutral
        FROM sentiment_posts
        WHERE asset = %s
        AND scraped_at > NOW() - INTERVAL '7 days'
        GROUP BY asset
    """, (asset.upper(),))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(result) if result else None

def answer_question(question: str) -> dict:
    relevant_posts = search_similar(question, k=TOP_K_RESULTS)

    if not relevant_posts:
        return {
            "answer": "I don't have enough data to answer that question yet.",
            "sources": []
        }

    context = "\n".join([
        f"- [{p['asset']} | {p['sentiment_label']} | score: {p['sentiment_score']:.2f}] {p['title']}"
        for p in relevant_posts
    ])

    asset_mentioned = "BTC"
    q_lower = question.lower()
    if "eth" in q_lower or "ethereum" in q_lower:
        asset_mentioned = "ETH"

    summary = get_sentiment_summary(asset_mentioned)
    summary_text = ""
    if summary:
        summary_text = f"""
Current {asset_mentioned} sentiment summary (last 7 days):
- Total posts analyzed: {summary['total']}
- Average sentiment score: {summary['avg_score']}
- Positive: {summary['positive']} | Negative: {summary['negative']} | Neutral: {summary['neutral']}
"""

    prompt = f"""You are a cryptocurrency sentiment analyst chatbot.
Answer the user's question based on the Reddit posts and sentiment data provided.
Be concise, informative, and mention specific sentiment scores when relevant.

{summary_text}

Most relevant Reddit posts:
{context}

User question: {question}

Provide a clear, helpful answer based on the sentiment data above."""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a helpful cryptocurrency sentiment analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=500
    )

    return {
        "answer": response.choices[0].message.content,
        "sources": [
            {
                "title":     p['title'],
                "asset":     p['asset'],
                "sentiment": p['sentiment_label'],
                "score":     p['sentiment_score'],
                "subreddit": p['subreddit']
            }
            for p in relevant_posts
        ]
    }