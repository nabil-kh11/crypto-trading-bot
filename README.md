# Advanced Crypto Trading Bot Platform

Final year internship project — microservices-based algorithmic trading platform for BTC/USDT and ETH/USDT.

## Architecture
Microservices communicating via REST API and RabbitMQ message queue, orchestrated with Kubernetes.

## Services
| Service | Description | Tech |
|---|---|---|
| market-data-collector | Real-time OHLCV ingestion from Binance | Python, ccxt, WebSocket |
| ml-decision-engine | Buy/sell/hold signal generation | Python, FastAPI, XGBoost |
| sentiment-collector | Reddit scraping + FinBERT scoring | Python, PRAW, FinBERT |
| order-executor | Paper trading execution | Python, FastAPI, RabbitMQ |
| chatbot | RAG-powered sentiment chatbot | Python, LangChain, FAISS |
| dashboard | Frontend visualization | Next.js, Chart.js |

## Stack
| Layer | Tools |
|---|---|
| Backend | Python, FastAPI |
| Frontend | Next.js, Chart.js |
| ML | XGBoost, Random Forest, PyTorch, scikit-learn |
| Messaging | RabbitMQ |
| Storage | PostgreSQL |
| DevOps | Docker, Kubernetes, Jenkins, SonarQube |
| Monitoring | Prometheus, Grafana |

## Data
- 10,000 rows of BTC/USDT OHLCV (1h timeframe) from Binance
- 10,000 rows of ETH/USDT OHLCV (1h timeframe) from Binance

## Project Structure
```
crypto-trading-bot/
├── services/        # One folder per microservice
├── infrastructure/  # Docker, Kubernetes, monitoring configs
├── data/            # Raw data, processed data, trained models
├── docs/            # Architecture diagrams and documentation
└── notebooks/       # ML experimentation and analysis
```

## Setup
```bash
cp .env.example .env
# Fill in your API keys in .env
"# CI/CD Test" 
