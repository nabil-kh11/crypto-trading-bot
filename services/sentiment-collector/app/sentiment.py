from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from app.config import SUBREDDITS

# Use VADER for fast sentiment analysis
# FinBERT can be added later as improvement
analyzer = SentimentIntensityAnalyzer()

ASSET_KEYWORDS = {
    "BTC": ["bitcoin", "btc", "₿"],
    "ETH": ["ethereum", "eth", "ether"],
}

def analyze_sentiment(text: str) -> dict:
    scores = analyzer.polarity_scores(text)
    compound = scores['compound']

    if compound >= 0.05:
        label = "POSITIVE"
    elif compound <= -0.05:
        label = "NEGATIVE"
    else:
        label = "NEUTRAL"

    return {
        "label": label,
        "score": round(compound, 4)
    }

def detect_asset(text: str) -> str:
    text_lower = text.lower()
    for asset, keywords in ASSET_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return asset
    return "GENERAL"

def process_post(post: dict) -> dict:
    text = f"{post.get('title', '')} {post.get('body', '')}"
    sentiment = analyze_sentiment(text)
    asset = detect_asset(text)

    return {
        **post,
        "sentiment_label": sentiment["label"],
        "sentiment_score": sentiment["score"],
        "asset": asset
    }