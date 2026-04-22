"""
Locust stress test for crypto trading bot
Tests all order-executor and market-data endpoints under load
"""
from locust import HttpUser, task, between

class OrderExecutorUser(HttpUser):
    """Simulates users hitting the order-executor service"""
    host = "http://localhost:8004"
    wait_time = between(1, 3)  # wait 1-3s between requests

    @task(3)
    def get_signal_btc(self):
        self.client.get("/signal/BTC-USDT", name="/signal/BTC-USDT")

    @task(3)
    def get_signal_eth(self):
        self.client.get("/signal/ETH-USDT", name="/signal/ETH-USDT")

    @task(2)
    def get_balance(self):
        self.client.get("/balance", name="/balance")

    @task(2)
    def get_trades(self):
        self.client.get("/trades?limit=50", name="/trades")

    @task(1)
    def get_health(self):
        self.client.get("/health", name="/health")


class MarketDataUser(HttpUser):
    """Simulates users hitting the market-data service"""
    host = "http://localhost:8001"
    wait_time = between(1, 2)

    @task(3)
    def get_price_btc(self):
        self.client.get("/price/BTC-USDT", name="/price/BTC-USDT")

    @task(3)
    def get_price_eth(self):
        self.client.get("/price/ETH-USDT", name="/price/ETH-USDT")

    @task(1)
    def get_health(self):
        self.client.get("/health", name="/health")