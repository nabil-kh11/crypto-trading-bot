import os
from dotenv import load_dotenv

load_dotenv()

# Reddit API credentials
REDDIT_CLIENT_ID     = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT    = os.getenv("REDDIT_USER_AGENT", "crypto-sentiment-bot/1.0")

# Subreddits to scrape
SUBREDDITS = ["Bitcoin", "ethereum", "CryptoCurrency"]

# PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:admin@localhost:5432/cryptobot")
# Service
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8003))

# Scraping settings
POSTS_PER_SUBREDDIT = 100
SCRAPE_INTERVAL_MINUTES = 60