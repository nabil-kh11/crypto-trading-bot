FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir fastapi uvicorn psycopg2-binary python-dotenv groq
RUN pip install --no-cache-dir faiss-cpu
RUN pip install --no-cache-dir sentence-transformers

COPY app/ ./app/

EXPOSE 8005

CMD ["python", "-m", "app.main"]