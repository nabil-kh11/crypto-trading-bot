FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir fastapi uvicorn psycopg2-binary python-dotenv
RUN pip install --no-cache-dir groq
RUN pip install --no-cache-dir faiss-cpu
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir transformers sentence-transformers
RUN pip install --no-cache-dir grpcio protobuf
RUN pip install --no-cache-dir prometheus-fastapi-instrumentator
# Pre-download sentence-transformers model
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
COPY app/ ./app/
# Pre-build FAISS index at build time — startup will be instant
COPY prebuild_index.py .
RUN python prebuild_index.py
EXPOSE 8005
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8005"]