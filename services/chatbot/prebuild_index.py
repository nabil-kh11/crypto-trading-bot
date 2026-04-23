"""
Pre-build script — runs at Docker build time to create FAISS index
from mock data so startup is instant (no 4-minute wait).
"""
import os
import sys
import pickle
import numpy as np

# Add app to path
sys.path.insert(0, '/app')

print("Pre-building FAISS index from mock data...")

# ── Generate mock posts (same logic as mock_data.py but no DB needed) ──────
import random
import datetime

MOCK_POSTS = [
    ("Bitcoin is showing incredible strength today, breaking above $70k resistance!", "Bitcoin", "BTC", "POSITIVE", 0.85),
    ("BTC hodlers being rewarded, long term outlook remains extremely bullish", "Bitcoin", "BTC", "POSITIVE", 0.78),
    ("Bitcoin adoption is accelerating, major corporations adding BTC to treasury", "Bitcoin", "BTC", "POSITIVE", 0.82),
    ("BTC mining difficulty hits all time high showing network is stronger than ever", "Bitcoin", "BTC", "POSITIVE", 0.71),
    ("Lightning network growing rapidly, Bitcoin payments becoming mainstream", "Bitcoin", "BTC", "POSITIVE", 0.76),
    ("Institutional investors piling into Bitcoin, demand outstripping supply", "Bitcoin", "BTC", "POSITIVE", 0.88),
    ("Bitcoin dominance rising, crypto market rotating into BTC safety", "Bitcoin", "BTC", "POSITIVE", 0.65),
    ("BTC on chain metrics looking incredibly bullish, accumulation phase confirmed", "Bitcoin", "BTC", "POSITIVE", 0.79),
    ("Bitcoin halving effect kicking in, supply shock incoming", "Bitcoin", "BTC", "POSITIVE", 0.83),
    ("Major bank announces Bitcoin custody service, institutional adoption growing", "Bitcoin", "BTC", "POSITIVE", 0.87),
    ("BTC breaking out of consolidation pattern, next target is $80k", "Bitcoin", "BTC", "POSITIVE", 0.74),
    ("Bitcoin network hash rate at all time high, security never been better", "Bitcoin", "BTC", "POSITIVE", 0.69),
    ("Bitcoin crashing hard, lost 15% in last 24 hours, panic selling everywhere", "Bitcoin", "BTC", "NEGATIVE", -0.82),
    ("BTC looking extremely bearish, head and shoulders pattern forming", "Bitcoin", "BTC", "NEGATIVE", -0.75),
    ("Bitcoin regulation fears mounting as governments crack down on crypto", "Bitcoin", "BTC", "NEGATIVE", -0.71),
    ("BTC miners selling heavily, putting downward pressure on price", "Bitcoin", "BTC", "NEGATIVE", -0.68),
    ("BTC breaking below key support, next stop could be $50k", "Bitcoin", "BTC", "NEGATIVE", -0.79),
    ("Bitcoin whales dumping, retail investors left holding the bag", "Bitcoin", "BTC", "NEGATIVE", -0.83),
    ("Crypto exchange hack causes Bitcoin fear across entire market", "Bitcoin", "BTC", "NEGATIVE", -0.88),
    ("Bitcoin bear market confirmed, down 40% from all time high", "Bitcoin", "BTC", "NEGATIVE", -0.85),
    ("Bitcoin trading sideways, consolidating between $65k and $70k", "Bitcoin", "BTC", "NEUTRAL", 0.05),
    ("BTC volume declining, market awaiting next catalyst", "Bitcoin", "BTC", "NEUTRAL", -0.02),
    ("Bitcoin holding key support, neither bullish nor bearish right now", "Bitcoin", "BTC", "NEUTRAL", 0.03),
    ("Ethereum upgrade successful, gas fees dropping significantly!", "ethereum", "ETH", "POSITIVE", 0.88),
    ("ETH staking rewards looking attractive, validators earning good yield", "ethereum", "ETH", "POSITIVE", 0.76),
    ("Ethereum DeFi ecosystem booming, TVL hitting new highs", "ethereum", "ETH", "POSITIVE", 0.82),
    ("ETH burn rate accelerating, becoming more deflationary than ever", "ethereum", "ETH", "POSITIVE", 0.79),
    ("Ethereum layer 2 adoption exploding, transaction costs near zero", "ethereum", "ETH", "POSITIVE", 0.84),
    ("ETH institutional demand surging ahead of spot ETF approval", "ethereum", "ETH", "POSITIVE", 0.87),
    ("Ethereum gas fees spiking again, network congestion is back", "ethereum", "ETH", "NEGATIVE", -0.72),
    ("ETH crashing alongside Bitcoin, no safe haven in crypto", "ethereum", "ETH", "NEGATIVE", -0.78),
    ("Ethereum competitors gaining market share, ETH dominance declining", "ethereum", "ETH", "NEGATIVE", -0.65),
    ("Ethereum DeFi hack drains millions, security concerns growing", "ethereum", "ETH", "NEGATIVE", -0.85),
    ("Ethereum consolidating after recent move, direction unclear", "ethereum", "ETH", "NEUTRAL", 0.02),
    ("ETH trading volume below average, market waiting for catalyst", "ethereum", "ETH", "NEUTRAL", -0.03),
    ("Crypto market showing signs of recovery after recent dip", "CryptoCurrency", "GENERAL", "POSITIVE", 0.65),
    ("Total crypto market cap back above $2 trillion", "CryptoCurrency", "GENERAL", "POSITIVE", 0.72),
    ("Crypto market bloodbath today, everything down double digits", "CryptoCurrency", "GENERAL", "NEGATIVE", -0.85),
    ("Regulatory crackdown on crypto exchanges causing market panic", "CryptoCurrency", "GENERAL", "NEGATIVE", -0.79),
    ("Crypto market stable, Bitcoin and Ethereum holding key levels", "CryptoCurrency", "GENERAL", "NEUTRAL", 0.03),
]

# Generate 1000 variations
price_levels_btc = ["$60k", "$65k", "$70k", "$75k", "$80k", "$85k", "$90k", "$100k"]
price_levels_eth = ["$1500", "$2000", "$2500", "$3000", "$3500", "$4000", "$4500"]
timeframes = ["today", "this week", "this month", "in the last 24 hours", "this morning"]

extended = []
base_time = datetime.datetime.now() - datetime.timedelta(days=30)

while len(extended) < 1000:
    for title, subreddit, asset, label, score in MOCK_POSTS:
        if len(extended) >= 1000:
            break
        variation = title
        if asset == "BTC" and random.random() > 0.5:
            variation = variation.replace("$70k", random.choice(price_levels_btc))
        if asset == "ETH" and random.random() > 0.5:
            variation = variation.replace("$3500", random.choice(price_levels_eth))
        variation = f"{variation} - {random.choice(timeframes)}"
        score_v = max(-1.0, min(1.0, score + random.uniform(-0.05, 0.05)))
        post_time = base_time + datetime.timedelta(hours=len(extended) * 0.72)
        extended.append({
            "id": len(extended) + 1,
            "title": variation,
            "body": variation,
            "asset": asset,
            "sentiment_label": label,
            "sentiment_score": score_v,
            "subreddit": subreddit,
            "created_utc": post_time,
        })

print(f"Generated {len(extended)} mock posts")

# ── Build FAISS index ──────────────────────────────────────────────────────
from sentence_transformers import SentenceTransformer
import faiss

model = SentenceTransformer("all-MiniLM-L6-v2")
texts = [f"{p['title']} {p['body']}" for p in extended]

print("Encoding embeddings...")
embeddings = model.encode(texts, show_progress_bar=True)
embeddings = np.array(embeddings).astype('float32')

dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# ── Save to disk ───────────────────────────────────────────────────────────
os.makedirs('/app/data', exist_ok=True)
faiss.write_index(index, '/app/data/faiss.index')
with open('/app/data/posts.pkl', 'wb') as f:
    pickle.dump(extended, f)

print(f"Saved FAISS index ({index.ntotal} vectors) and posts to /app/data/")
print("Pre-build complete!")