FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install ALL requirements
COPY services/ml-decision-engine/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app and models
COPY services/ml-decision-engine/app/ ./app/
COPY data/models/ ./data/models/

EXPOSE 8002

CMD ["python", "-m", "app.main"]