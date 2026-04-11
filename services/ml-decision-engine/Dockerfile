FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY services/ml-decision-engine/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY services/ml-decision-engine/app/ ./app/

# Copy models from top-level data directory (if exists)
COPY data/models/ ./data/models/

EXPOSE 8002

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]