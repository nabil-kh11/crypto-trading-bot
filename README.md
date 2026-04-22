# 🤖 AI-Powered Cryptocurrency Trading Bot

> Microservices-based algorithmic trading platform for BTC/USDT and ETH/USDT using Machine Learning, real-time market data, and automated paper trading — Final Year Internship Project.

---

## 🎯 Overview

| Property | Value |
|----------|-------|
| Assets | BTC/USDT, ETH/USDT |
| Data Source | Binance API (real-time + historical) |
| ML Models | Neural Network (BTC), XGBoost (ETH) |
| Architecture | 8 microservices — REST + gRPC + RabbitMQ |
| Trading | Binance Testnet (10,000 USDT paper balance) |
| Gateway | Nginx (port 8090) |
| Dashboard | Next.js (port 33000) |

---

## 🏗 Architecture

```
                    ┌──────────────────────────────┐
                    │      Nginx Gateway :8090      │
                    │  reverse proxy + rate limit   │
                    └──────────────┬───────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────┐
        ▼                          ▼                       ▼
┌───────────────┐      ┌───────────────────┐     ┌─────────────────┐
│ market-data   │─────▶│ ml-decision-engine│────▶│ order-executor  │
│ :8001/:50051  │ gRPC │ :8002 / :50052    │gRPC │ :8004 / :50054  │
│ 35 indicators │      │ XGBoost + NN      │     │ Binance Testnet │
└───────────────┘      └───────────────────┘     └────────┬────────┘
                                                           │
                                                    ┌──────▼──────┐
        ┌──────────────┐     ┌─────────────┐        │  RabbitMQ   │
        │  sentiment   │     │   chatbot   │        │   :5672     │
        │ :8003/:50053 │     │ :8005/:50055│        └──────┬──────┘
        │ VADER+Reddit │     │ RAG + Groq  │               │
        └──────────────┘     └─────────────┘               ▼
                                                    ┌──────────────┐
                                                    │  PostgreSQL  │
                                                    │    :5432     │
                                                    └──────┬───────┘
                                                           │
                                                    ┌──────▼───────┐
                                                    │  dashboard   │
                                                    │   :33000     │
                                                    │ Next.js + P&L│
                                                    └──────────────┘
```

---

## 🛠 Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python 3.12, FastAPI, Uvicorn |
| **ML** | Neural Network, XGBoost, scikit-learn, joblib |
| **Data** | pandas, numpy, ta, ccxt |
| **Communication** | gRPC, REST, RabbitMQ (AMQP) |
| **Frontend** | Next.js, Chart.js, WebSocket |
| **Database** | PostgreSQL 15 |
| **Gateway** | Nginx (REST proxy + gRPC TCP proxy) |
| **Containers** | Docker, Docker Compose |
| **Orchestration** | Kubernetes (Docker Desktop), Helm |
| **CI/CD** | Jenkins, SonarQube |
| **Monitoring** | Prometheus, Grafana |
| **NLP** | VADER, sentence-transformers, FAISS |
| **LLM** | Groq API (LLaMA) |
| **Testing** | pytest (42 tests), Locust (stress testing) |

---

## 🔧 Services

| Service | REST | gRPC | Role |
|---------|------|------|------|
| `market-data-collector` | 8001 | 50051 | Live OHLCV from Binance + 35 technical indicators |
| `ml-decision-engine` | 8002 | 50052 | XGBoost/Neural Network → BUY/SELL/HOLD + confidence |
| `sentiment-collector` | 8003 | 50053 | Reddit scraper + VADER sentiment scoring |
| `order-executor` | 8004 | 50054 | Trade execution + risk management + audit logging |
| `chatbot` | 8005 | 50055 | RAG Q&A using FAISS + sentence-transformers + Groq |
| `dashboard` | 33000 | — | Next.js: live charts, strategy selector, P&L |
| `rabbitmq` | 5672 | — | Async signal publishing between services |
| `postgres` | 5432 | — | Trades, signals, sentiment persistence |
| `nginx` | 8090 | — | API gateway, rate limiting, gRPC TCP proxy |

---

## 📁 Project Structure

```
crypto-trading-bot/
├── services/
│   ├── market-data-collector/
│   ├── ml-decision-engine/
│   ├── sentiment-collector/
│   ├── order-executor/          # includes audit_logger.py
│   ├── chatbot/
│   └── dashboard/               # Next.js
│
├── infrastructure/
│   ├── docker/
│   ├── grpc/
│   ├── jenkins/
│   ├── kubernetes/
│   │   ├── base/                # K8s manifests + secret.yaml
│   │   └── helm/                # Helm chart
│   ├── monitoring/
│   │   ├── prometheus/
│   │   └── grafana/
│   └── nginx/
│
├── tests/
│   ├── unit/                    # pytest — 42 tests
│   ├── integration/
│   ├── locustfile.py
│   ├── locust_results_stats.csv
│   └── locust_results_failures.csv
│
├── data/
│   ├── raw/                     # Binance CSVs (10,000 bars each)
│   ├── processed/               # train/test splits
│   └── models/                  # .joblib trained models
│
├── notebooks/
│   ├── 01_etl.ipynb
│   ├── 02_ml_training.ipynb
│   ├── 03_backtesting.ipynb
│   └── 04_live_test.ipynb
│
├── proto/                       # gRPC .proto definitions
├── logs/
│   └── order-executor/
│       └── audit.log            # JSONL audit trail
├── docs/
│   └── diagrams/
├── docker-compose.yml
├── Jenkinsfile
├── kubeconfig.yaml
├── .env
└── .env.example
```

---

## 🚀 Quick Start

```bash
cp .env.example .env
# Add your Binance Testnet API keys to .env

docker compose up -d
docker compose ps
```

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:33000 |
| API Gateway | http://localhost:8090 |
| RabbitMQ UI | http://localhost:15672 (guest/guest) |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 (admin/admin) |

---

## 📈 Trading Strategies

| Strategy | Min Confidence | Stop Loss | Take Profit (3 levels) | Min Hold |
|----------|---------------|-----------|------------------------|----------|
| **Scalping** | 35% | 2% | 2% / 4% / 6% | None |
| **Swing** | 50% | 5% | 10% / 15% / 20% | 4h |
| **Position** | 70% | 10% | 20% / 30% / 50% | 24h |
| **Off** | — | — | — | Disabled |

Risk management: Kelly Criterion sizing · trailing stop · ATR volatility factor · RSI filter · trend filter (MA20/MA50) · volume filter · daily loss limit.

---

## 🧠 ML Models

| Symbol | Model | Features | Dataset |
|--------|-------|----------|---------|
| BTC/USDT | Neural Network | 35 | 10,000 hourly bars |
| ETH/USDT | XGBoost | 35 | 10,000 hourly bars |

Features: MA20/50/200 · RSI · MACD · Bollinger Bands · ATR · StochRSI · volume ratio · lag features (1/2/3/6/12/24h) · hour · day of week.

---

## 🧪 Testing

```bash
# Unit tests
pytest tests/unit/ -v --cov=services

# Stress test — 50 users (baseline)
python -m locust -f tests/locustfile.py --headless -u 50 -r 5 -t 60s --only-summary

# Stress test — 200 users
python -m locust -f tests/locustfile.py --headless -u 200 -r 10 -t 60s --only-summary
```

| Test | Users | Requests | Failures | Throughput |
|------|-------|----------|----------|------------|
| Baseline | 50 | 1,043 | 0 (0.00%) | 17.53 req/s |
| Stress | 200 | 2,482 | 2 (0.08%) | 41.58 req/s |

---

## 🔄 CI/CD Pipeline

```
Checkout → Detect Changes → Build → Unit Tests → Integration Tests → SonarQube → Deploy (Helm) → Verify
```

## ☸️ Kubernetes Deployment

```bash
helm install crypto-trading-bot infrastructure/kubernetes/helm/crypto-trading-bot
kubectl get pods -n crypto-trading-bot
```

Features: HPA auto-scaling (ml-decision-engine: 1→3, order-executor: 1→2 replicas at 70% CPU) · Blue-Green deployment for 5 services (ml-engine, order-executor, chatbot, market-data, sentiment) · Kubernetes Secrets (app-secrets: 3 credentials)

---

## 📊 Monitoring

| Tool | URL | Purpose |
|------|-----|---------|
| Grafana | :3001 | Latency, trade stats, ML confidence, errors |
| Prometheus | :9090 | Metrics scraping from all services |
| RabbitMQ UI | :15672 | Queue monitoring |
| Audit Log | `logs/order-executor/audit.log` | Every trade decision |

---

## 📋 Audit Logging

Every trade decision logged as structured JSONL in `logs/order-executor/audit.log`:

```json
{"timestamp": "2026-04-22T19:04:39Z", "event": "STRATEGY_CHANGED", "from": "swing", "to": "scalping"}
{"timestamp": "2026-04-22T19:05:53Z", "event": "SIGNAL_RECEIVED", "symbol": "BTC/USDT", "signal": "HOLD", "confidence": 45.08, "model": "Neural Network", "price": 78828.04}
{"timestamp": "2026-04-22T19:07:01Z", "event": "TRADE_EXECUTED", "symbol": "BTC/USDT", "signal": "BUY", "price": 78802.51, "quantity": 0.00063, "invested_usdt": 49.5}
```

Events: `SIGNAL_RECEIVED` · `TRADE_EXECUTED` · `TRADE_FILTERED` · `STOP_LOSS_TRIGGERED` · `STRATEGY_CHANGED` · `HOLD` · `TRADE_ERROR`

```bash
findstr "TRADE_EXECUTED"   logs\order-executor\audit.log
findstr "STRATEGY_CHANGED" logs\order-executor\audit.log
findstr "STOP_LOSS"        logs\order-executor\audit.log
```

---

**Nabil Khiari** · Final Year Internship · April 2026