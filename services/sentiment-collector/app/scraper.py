import praw
import datetime
from app.config import (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET,
                         REDDIT_USER_AGENT, SUBREDDITS, POSTS_PER_SUBREDDIT)
from app.sentiment import process_post
from app.database import save_post

MOCK_POSTS = [
    {"title": "Bitcoin is looking bullish today!", "body": "BTC just broke resistance at 70k", "subreddit": "Bitcoin", "score": 150, "num_comments": 45},
    {"title": "Ethereum network upgrade coming soon", "body": "ETH developers announced major improvements", "subreddit": "ethereum", "score": 200, "num_comments": 67},
    {"title": "Crypto market is crashing hard", "body": "Bitcoin down 10% in last hour, panic selling", "subreddit": "CryptoCurrency", "score": 89, "num_comments": 123},
    {"title": "BTC holding strong above 70k support", "body": "Long term holders are not selling bitcoin", "subreddit": "Bitcoin", "score": 310, "num_comments": 88},
    {"title": "ETH gas fees are too high again", "body": "Ethereum transactions cost too much", "subreddit": "ethereum", "score": 45, "num_comments": 34},
]

def get_reddit_client():
    if not REDDIT_CLIENT_ID:
        return None
    return praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )

def scrape_subreddit(subreddit_name: str, limit: int = POSTS_PER_SUBREDDIT):
    reddit = get_reddit_client()

    if not reddit:
        print(f"No Reddit credentials — using mock data for {subreddit_name}")
        return scrape_mock(subreddit_name)

    posts = []
    subreddit = reddit.subreddit(subreddit_name)

    for post in subreddit.hot(limit=limit):
        posts.append({
            "post_id":      post.id,
            "subreddit":    subreddit_name,
            "title":        post.title,
            "body":         post.selftext[:1000] if post.selftext else "",
            "score":        post.score,
            "num_comments": post.num_comments,
            "created_utc":  datetime.datetime.fromtimestamp(post.created_utc),
        })

    return posts

def scrape_mock(subreddit_name: str):
    import uuid
    posts = []
    for mock in MOCK_POSTS:
        if mock["subreddit"] == subreddit_name:
            posts.append({
                "post_id":      str(uuid.uuid4())[:8],
                "subreddit":    subreddit_name,
                "title":        mock["title"],
                "body":         mock["body"],
                "score":        mock["score"],
                "num_comments": mock["num_comments"],
                "created_utc":  datetime.datetime.now(),
            })
    return posts

def scrape_and_save_all():
    total = 0
    for subreddit in SUBREDDITS:
        posts = scrape_subreddit(subreddit)
        for post in posts:
            processed = process_post(post)
            save_post(processed)
            total += 1
    print(f"Scraped and saved {total} posts")
    return total