import sys
import os
import pytest
import grpc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../proto'))

import ml_engine_pb2
import ml_engine_pb2_grpc
import market_data_pb2
import market_data_pb2_grpc
import order_executor_pb2
import order_executor_pb2_grpc
import sentiment_pb2
import sentiment_pb2_grpc
import chatbot_pb2
import chatbot_pb2_grpc

GRPC_HOST = os.getenv('GRPC_HOST', 'localhost')
NGINX_HOST = os.getenv('NGINX_HOST', 'localhost')

class TestGRPCGateway:

    def test_market_data_via_nginx(self):
        """Market data reachable via Nginx gRPC proxy"""
        channel = grpc.insecure_channel(f'{NGINX_HOST}:9051')
        stub = market_data_pb2_grpc.MarketDataServiceStub(channel)
        response = stub.GetHealth(market_data_pb2.HealthRequest(), timeout=5)
        assert response.status == 'ok'

    def test_ml_engine_via_nginx(self):
        """ML engine reachable via Nginx gRPC proxy"""
        channel = grpc.insecure_channel(f'{NGINX_HOST}:9052')
        stub = ml_engine_pb2_grpc.MLEngineServiceStub(channel)
        response = stub.GetHealth(ml_engine_pb2.HealthRequest(), timeout=5)
        assert response.status == 'ok'

    def test_sentiment_via_nginx(self):
        """Sentiment reachable via Nginx gRPC proxy"""
        channel = grpc.insecure_channel(f'{NGINX_HOST}:9053')
        stub = sentiment_pb2_grpc.SentimentServiceStub(channel)
        response = stub.GetHealth(sentiment_pb2.HealthRequest(), timeout=5)
        assert response.status == 'ok'

    def test_order_executor_via_nginx(self):
        """Order executor reachable via Nginx gRPC proxy"""
        channel = grpc.insecure_channel(f'{NGINX_HOST}:9054')
        stub = order_executor_pb2_grpc.OrderExecutorServiceStub(channel)
        response = stub.GetHealth(order_executor_pb2.HealthRequest(), timeout=5)
        assert response.status == 'ok'

    def test_chatbot_via_nginx(self):
        """Chatbot reachable via Nginx gRPC proxy"""
        channel = grpc.insecure_channel(f'{NGINX_HOST}:9055')
        stub = chatbot_pb2_grpc.ChatbotServiceStub(channel)
        response = stub.GetHealth(chatbot_pb2.HealthRequest(), timeout=5)
        assert response.status == 'ok'

    def test_market_data_price_via_nginx(self):
        """Get BTC price via Nginx gRPC proxy"""
        channel = grpc.insecure_channel(f'{NGINX_HOST}:9051')
        stub = market_data_pb2_grpc.MarketDataServiceStub(channel)
        response = stub.GetPrice(
            market_data_pb2.PriceRequest(symbol='BTC-USDT'), timeout=5
        )
        assert response.price > 0