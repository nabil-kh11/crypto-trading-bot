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

class TestDirectGRPC:

    def test_market_data_health(self):
        """Market data gRPC server is healthy"""
        channel = grpc.insecure_channel(f'{GRPC_HOST}:50051')
        stub = market_data_pb2_grpc.MarketDataServiceStub(channel)
        response = stub.GetHealth(market_data_pb2.HealthRequest(), timeout=5)
        assert response.status == 'ok'

    def test_ml_engine_health(self):
        """ML engine gRPC server is healthy"""
        channel = grpc.insecure_channel(f'{GRPC_HOST}:50052')
        stub = ml_engine_pb2_grpc.MLEngineServiceStub(channel)
        response = stub.GetHealth(ml_engine_pb2.HealthRequest(), timeout=5)
        assert response.status == 'ok'

    def test_sentiment_health(self):
        """Sentiment gRPC server is healthy"""
        channel = grpc.insecure_channel(f'{GRPC_HOST}:50053')
        stub = sentiment_pb2_grpc.SentimentServiceStub(channel)
        response = stub.GetHealth(sentiment_pb2.HealthRequest(), timeout=5)
        assert response.status == 'ok'

    def test_order_executor_health(self):
        """Order executor gRPC server is healthy"""
        channel = grpc.insecure_channel(f'{GRPC_HOST}:50054')
        stub = order_executor_pb2_grpc.OrderExecutorServiceStub(channel)
        response = stub.GetHealth(order_executor_pb2.HealthRequest(), timeout=5)
        assert response.status == 'ok'

    def test_chatbot_health(self):
        """Chatbot gRPC server is healthy"""
        channel = grpc.insecure_channel(f'{GRPC_HOST}:50055')
        stub = chatbot_pb2_grpc.ChatbotServiceStub(channel)
        response = stub.GetHealth(chatbot_pb2.HealthRequest(), timeout=5)
        assert response.status == 'ok'

    def test_market_data_get_price_btc(self):
        """Market data returns BTC price"""
        channel = grpc.insecure_channel(f'{GRPC_HOST}:50051')
        stub = market_data_pb2_grpc.MarketDataServiceStub(channel)
        response = stub.GetPrice(
            market_data_pb2.PriceRequest(symbol='BTC-USDT'), timeout=5
        )
        assert response.price > 0

    def test_market_data_get_price_eth(self):
        """Market data returns ETH price"""
        channel = grpc.insecure_channel(f'{GRPC_HOST}:50051')
        stub = market_data_pb2_grpc.MarketDataServiceStub(channel)
        response = stub.GetPrice(
            market_data_pb2.PriceRequest(symbol='ETH-USDT'), timeout=5
        )
        assert response.price > 0

    def test_ml_engine_get_symbols(self):
        """ML engine returns supported symbols"""
        channel = grpc.insecure_channel(f'{GRPC_HOST}:50052')
        stub = ml_engine_pb2_grpc.MLEngineServiceStub(channel)
        response = stub.GetSymbols(ml_engine_pb2.SymbolsRequest(), timeout=5)
        assert len(response.symbols) > 0
        assert 'BTC/USDT' in response.symbols