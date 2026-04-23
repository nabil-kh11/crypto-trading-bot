import random
import datetime
import psycopg2
from app.config import DATABASE_URL

MOCK_POSTS = [
    # BTC Positive
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
    ("Grayscale Bitcoin trust seeing massive inflows from institutional investors", "Bitcoin", "BTC", "POSITIVE", 0.81),
    ("BTC RSI not yet overbought, plenty of room to run higher", "Bitcoin", "BTC", "POSITIVE", 0.72),
    ("Bitcoin solving real world problems with censorship resistant payments", "Bitcoin", "BTC", "POSITIVE", 0.68),
    # BTC Negative
    ("Bitcoin crashing hard, lost 15% in last 24 hours, panic selling everywhere", "Bitcoin", "BTC", "NEGATIVE", -0.82),
    ("BTC looking extremely bearish, head and shoulders pattern forming", "Bitcoin", "BTC", "NEGATIVE", -0.75),
    ("Bitcoin regulation fears mounting as governments crack down on crypto", "Bitcoin", "BTC", "NEGATIVE", -0.71),
    ("BTC miners selling heavily, putting downward pressure on price", "Bitcoin", "BTC", "NEGATIVE", -0.68),
    ("Bitcoin energy consumption criticism growing, ESG concerns hurting adoption", "Bitcoin", "BTC", "NEGATIVE", -0.65),
    ("BTC breaking below key support, next stop could be $50k", "Bitcoin", "BTC", "NEGATIVE", -0.79),
    ("Bitcoin whales dumping, retail investors left holding the bag", "Bitcoin", "BTC", "NEGATIVE", -0.83),
    ("Crypto exchange hack causes Bitcoin fear across entire market", "Bitcoin", "BTC", "NEGATIVE", -0.88),
    ("BTC transaction fees surging making small payments uneconomical", "Bitcoin", "BTC", "NEGATIVE", -0.61),
    ("Bitcoin bear market confirmed, down 40% from all time high", "Bitcoin", "BTC", "NEGATIVE", -0.85),
    ("FUD spreading fast, Bitcoin could test $40k support level", "Bitcoin", "BTC", "NEGATIVE", -0.77),
    ("BTC correction deepening, technical analysis points to further downside", "Bitcoin", "BTC", "NEGATIVE", -0.72),
    ("Bitcoin losing market share to altcoins, dominance declining", "Bitcoin", "BTC", "NEGATIVE", -0.58),
    ("Major country bans Bitcoin, regulatory risk increasing globally", "Bitcoin", "BTC", "NEGATIVE", -0.86),
    ("BTC liquidations cascade, over $500M wiped out in 1 hour", "Bitcoin", "BTC", "NEGATIVE", -0.91),
    # BTC Neutral
    ("Bitcoin trading sideways, consolidating between $65k and $70k", "Bitcoin", "BTC", "NEUTRAL", 0.05),
    ("BTC volume declining, market awaiting next catalyst", "Bitcoin", "BTC", "NEUTRAL", -0.02),
    ("Bitcoin holding key support, neither bullish nor bearish right now", "Bitcoin", "BTC", "NEUTRAL", 0.03),
    ("BTC price action choppy, mixed signals from technical indicators", "Bitcoin", "BTC", "NEUTRAL", 0.01),
    ("Bitcoin dominance stable at 52%, market in equilibrium", "Bitcoin", "BTC", "NEUTRAL", 0.04),
    # ETH Positive
    ("Ethereum upgrade successful, gas fees dropping significantly!", "ethereum", "ETH", "POSITIVE", 0.88),
    ("ETH staking rewards looking attractive, validators earning good yield", "ethereum", "ETH", "POSITIVE", 0.76),
    ("Ethereum DeFi ecosystem booming, TVL hitting new highs", "ethereum", "ETH", "POSITIVE", 0.82),
    ("ETH burn rate accelerating, becoming more deflationary than ever", "ethereum", "ETH", "POSITIVE", 0.79),
    ("Ethereum layer 2 adoption exploding, transaction costs near zero", "ethereum", "ETH", "POSITIVE", 0.84),
    ("ETH institutional demand surging ahead of spot ETF approval", "ethereum", "ETH", "POSITIVE", 0.87),
    ("Ethereum developer activity at all time high, ecosystem growing fast", "ethereum", "ETH", "POSITIVE", 0.73),
    ("ETH outperforming BTC this week, altseason may be starting", "ethereum", "ETH", "POSITIVE", 0.71),
    ("Ethereum NFT market recovering, blue chip projects gaining value", "ethereum", "ETH", "POSITIVE", 0.67),
    ("ETH breaking above $3500 resistance, targeting $4000 next", "ethereum", "ETH", "POSITIVE", 0.80),
    ("Ethereum staking yield beating traditional finance returns", "ethereum", "ETH", "POSITIVE", 0.75),
    ("ETH spot ETF approval imminent, price pumping on anticipation", "ethereum", "ETH", "POSITIVE", 0.89),
    ("Ethereum smart contract usage growing exponentially this quarter", "ethereum", "ETH", "POSITIVE", 0.70),
    ("ETH supply decreasing rapidly post merge, scarcity driving price", "ethereum", "ETH", "POSITIVE", 0.83),
    ("Ethereum foundation announces major protocol improvements", "ethereum", "ETH", "POSITIVE", 0.77),
    # ETH Negative
    ("Ethereum gas fees spiking again, network congestion is back", "ethereum", "ETH", "NEGATIVE", -0.72),
    ("ETH crashing alongside Bitcoin, no safe haven in crypto", "ethereum", "ETH", "NEGATIVE", -0.78),
    ("Ethereum competitors gaining market share, ETH dominance declining", "ethereum", "ETH", "NEGATIVE", -0.65),
    ("ETH staking withdrawal queue growing, liquid staking concerns rising", "ethereum", "ETH", "NEGATIVE", -0.61),
    ("Ethereum facing scalability issues despite layer 2 solutions", "ethereum", "ETH", "NEGATIVE", -0.68),
    ("ETH losing ground to Solana and other smart contract platforms", "ethereum", "ETH", "NEGATIVE", -0.74),
    ("Ethereum DeFi hack drains millions, security concerns growing", "ethereum", "ETH", "NEGATIVE", -0.85),
    ("ETH below $2000, critical support level being tested", "ethereum", "ETH", "NEGATIVE", -0.80),
    ("Ethereum regulatory uncertainty increasing, SEC scrutiny growing", "ethereum", "ETH", "NEGATIVE", -0.76),
    ("ETH underperforming Bitcoin, investors rotating to BTC safety", "ethereum", "ETH", "NEGATIVE", -0.63),
    ("Ethereum inflation concerns, staking rewards diluting holders", "ethereum", "ETH", "NEGATIVE", -0.58),
    ("ETH technical breakdown, 200 day moving average lost", "ethereum", "ETH", "NEGATIVE", -0.82),
    ("Ethereum bridge exploit causes massive ETH selloff", "ethereum", "ETH", "NEGATIVE", -0.88),
    ("ETH gas fees making DeFi unusable for small investors", "ethereum", "ETH", "NEGATIVE", -0.69),
    ("Ethereum network outage causes panic, validators missing blocks", "ethereum", "ETH", "NEGATIVE", -0.83),
    # ETH Neutral
    ("Ethereum consolidating after recent move, direction unclear", "ethereum", "ETH", "NEUTRAL", 0.02),
    ("ETH trading volume below average, market waiting for catalyst", "ethereum", "ETH", "NEUTRAL", -0.03),
    ("Ethereum price stable, neither buyers nor sellers in control", "ethereum", "ETH", "NEUTRAL", 0.01),
    ("ETH and BTC moving together, correlation at yearly high", "ethereum", "ETH", "NEUTRAL", 0.04),
    ("Ethereum market cap holding steady at current levels", "ethereum", "ETH", "NEUTRAL", 0.02),
    # General Crypto
    ("Crypto market showing signs of recovery after recent dip", "CryptoCurrency", "GENERAL", "POSITIVE", 0.65),
    ("Total crypto market cap back above $2 trillion", "CryptoCurrency", "GENERAL", "POSITIVE", 0.72),
    ("Crypto adoption in developing countries accelerating rapidly", "CryptoCurrency", "GENERAL", "POSITIVE", 0.78),
    ("Crypto market bloodbath today, everything down double digits", "CryptoCurrency", "GENERAL", "NEGATIVE", -0.85),
    ("Regulatory crackdown on crypto exchanges causing market panic", "CryptoCurrency", "GENERAL", "NEGATIVE", -0.79),
    ("Crypto market stable, Bitcoin and Ethereum holding key levels", "CryptoCurrency", "GENERAL", "NEUTRAL", 0.03),
    ("DeFi summer returning, yield farming opportunities expanding", "CryptoCurrency", "GENERAL", "POSITIVE", 0.81),
    ("Crypto winter fears growing as prices continue to decline", "CryptoCurrency", "GENERAL", "NEGATIVE", -0.76),
    ("Stablecoin market growing, more capital entering crypto ecosystem", "CryptoCurrency", "GENERAL", "POSITIVE", 0.69),
    ("Web3 development activity at all time high despite bear market", "CryptoCurrency", "GENERAL", "POSITIVE", 0.74),
]


def generate_extended_posts(base_posts, target=1000):
    """Generate extended dataset by creating variations of base posts"""
    extended = []

    price_levels_btc = ["$60k", "$65k", "$70k", "$75k", "$80k", "$85k", "$90k", "$100k"]
    price_levels_eth = ["$1500", "$2000", "$2500", "$3000", "$3500", "$4000", "$4500"]

    timeframes = ["today", "this week", "this month", "in the last 24 hours",
                  "this morning", "overnight", "in the past hour"]

    while len(extended) < target:
        for title, subreddit, asset, label, score in base_posts:
            if len(extended) >= target:
                break
            variation = title
            if asset == "BTC" and random.random() > 0.5:
                old_price = random.choice(price_levels_btc)
                new_price = random.choice(price_levels_btc)
                variation = variation.replace("$70k", old_price).replace("$80k", new_price)
            if asset == "ETH" and random.random() > 0.5:
                old_price = random.choice(price_levels_eth)
                new_price = random.choice(price_levels_eth)
                variation = variation.replace("$3500", old_price).replace("$4000", new_price)
            timeframe = random.choice(timeframes)
            variation = f"{variation} - {timeframe}"
            score_variation = score + random.uniform(-0.05, 0.05)
            score_variation = max(-1.0, min(1.0, score_variation))
            extended.append((variation, subreddit, asset, label, score_variation))

    return extended[:target]


def seed_database():
    """Seed the database with 1000+ mock posts"""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Create table if it doesn't exist (safe for fresh K8s PostgreSQL)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sentiment_posts (
            id SERIAL PRIMARY KEY,
            post_id VARCHAR(50) UNIQUE,
            subreddit VARCHAR(100),
            title TEXT,
            body TEXT,
            score INTEGER,
            num_comments INTEGER,
            created_utc TIMESTAMP,
            sentiment_label VARCHAR(20),
            sentiment_score FLOAT,
            asset VARCHAR(20),
            scraped_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM sentiment_posts")
    count = cursor.fetchone()[0]

    if count >= 100:
        print(f"Database already has {count} posts - skipping seed")
        cursor.close()
        conn.close()
        return count

    extended_posts = generate_extended_posts(MOCK_POSTS, target=1000)

    import uuid
    inserted = 0
    base_time = datetime.datetime.now() - datetime.timedelta(days=30)

    for i, (title, subreddit, asset, label, score) in enumerate(extended_posts):
        post_time = base_time + datetime.timedelta(hours=i * 0.72)
        try:
            cursor.execute("""
                INSERT INTO sentiment_posts
                (post_id, subreddit, title, body, score, num_comments,
                 created_utc, sentiment_label, sentiment_score, asset)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (post_id) DO NOTHING
            """, (
                str(uuid.uuid4())[:8],
                subreddit,
                title,
                title,
                random.randint(10, 5000),
                random.randint(5, 500),
                post_time,
                label,
                score,
                asset
            ))
            inserted += 1
        except Exception as e:
            print(f"Error inserting post: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Seeded database with {inserted} mock posts!")
    return inserted