import sys, os, importlib.util
from unittest.mock import MagicMock

sys.modules['praw'] = MagicMock()
sys.modules['psycopg2'] = MagicMock()

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'services', 'sentiment-collector', 'app')

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

sys.modules['app.config'] = MagicMock(SUBREDDITS=['CryptoCurrency'])
load('app.config', os.path.join(BASE, 'config.py'))
sentiment = load('app.sentiment', os.path.join(BASE, 'sentiment.py'))

analyze_sentiment = sentiment.analyze_sentiment
detect_asset      = sentiment.detect_asset
process_post      = sentiment.process_post

class TestSentimentAnalysis:
    def test_analyze_sentiment_positive(self):
        result = analyze_sentiment("Bitcoin is amazing and bullish!")
        assert result['label'] == "POSITIVE"

    def test_analyze_sentiment_negative(self):
        result = analyze_sentiment("Bitcoin is crashing and terrible!")
        assert result['label'] == "NEGATIVE"

    def test_analyze_sentiment_neutral(self):
        result = analyze_sentiment("Bitcoin price today is 73000")
        assert result['label'] == "NEUTRAL"

    def test_analyze_sentiment_returns_score(self):
        result = analyze_sentiment("Bitcoin is great!")
        assert 'label' in result and 'score' in result

    def test_analyze_sentiment_score_range(self):
        result = analyze_sentiment("Bitcoin is great!")
        assert -1.0 <= result['score'] <= 1.0

    def test_detect_asset_btc(self):
        assert detect_asset("Bitcoin is going up today") == "BTC"

    def test_detect_asset_eth(self):
        assert detect_asset("Ethereum merge was successful") == "ETH"

    def test_detect_asset_general(self):
        assert detect_asset("The market is looking good today") == "GENERAL"

    def test_process_post_returns_sentiment(self):
        post = {'title': 'Bitcoin is rising', 'body': 'Great news!'}
        result = process_post(post)
        assert 'sentiment_label' in result and result['asset'] == 'BTC'
    def test_analyze_sentiment_returns_model(self):
        """Sentiment returns model name"""
        result = analyze_sentiment("Bitcoin is great!")
        assert 'model' in result
        assert result['model'] in ['FinBERT', 'VADER']