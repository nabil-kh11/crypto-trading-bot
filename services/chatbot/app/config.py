import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv('/app/.env')

GROQ_API_KEY    = os.getenv("GROQ_API_KEY", "")
DATABASE_URL    = os.getenv("DATABASE_URL", "postgresql://postgres:admin@localhost:5432/cryptobot")
HOST            = os.getenv("HOST", "0.0.0.0")
PORT            = int(os.getenv("PORT", 8005))
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K_RESULTS   = 5