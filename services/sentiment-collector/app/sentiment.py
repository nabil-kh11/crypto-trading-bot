from app.config import SUBREDDITS
from transformers import pipeline
import torch

# FinBERT — financial domain BERT model
# Much more accurate than VADER for crypto/financial text
# Trained on financial news, earnings calls, analyst reports

print("[FinBERT] Loading financial sentiment model...")
try:
    finbert = pipeline(
        "sentiment-analysis",
        model="ProsusAI/finbert",
        device=-1  # CPU only (no GPU needed)
    )
    print("[FinBERT] Model loaded successfully!")
    USE_FINBERT = True
except Exception as e:
    print(f"[FinBERT] Failed to load: {e} — falling back to VADER")
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    vader_analyzer = SentimentIntensityAnalyzer()
    USE_FINBERT = False

ASSET_KEYWORDS = {
    "BTC": ["bitcoin", "btc", "₿"],
    "ETH": ["ethereum", "eth", "ether"],
}

def analyze_sentiment(text: str) -> dict:
    """Analyze sentiment using FinBERT (fallback to VADER)"""
    if USE_FINBERT:
        try:
            # FinBERT max token length is 512
            truncated = text[:512]
            result = finbert(truncated)[0]
            label = result['label'].upper()
            score = result['score']

            # FinBERT returns: positive, negative, neutral
            # Convert to signed score like VADER
            if label == 'POSITIVE':
                compound = round(score, 4)
            elif label == 'NEGATIVE':
                compound = round(-score, 4)
            else:
                compound = 0.0

            return {
                "label": label,
                "score": compound,
                "model": "FinBERT"
            }
        except Exception as e:
            print(f"[FinBERT] Inference error: {e} — using VADER")

    # VADER fallback
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    vader = SentimentIntensityAnalyzer()
    scores = vader.polarity_scores(text)
    compound = scores['compound']
    if compound >= 0.05:
        label = "POSITIVE"
    elif compound <= -0.05:
        label = "NEGATIVE"
    else:
        label = "NEUTRAL"
    return {
        "label": label,
        "score": round(compound, 4),
        "model": "VADER"
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
        "sentiment_model": sentiment.get("model", "unknown"),
        "asset": asset
    }