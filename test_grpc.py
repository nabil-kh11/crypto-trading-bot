import grpc
import sys
sys.path.insert(0, 'proto')

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

def test_all():
    tests = [
        ('ML Engine via Nginx gRPC',      'localhost:9052', ml_engine_pb2_grpc.MLEngineServiceStub,           ml_engine_pb2.HealthRequest()),
        ('Market Data via Nginx gRPC',    'localhost:9051', market_data_pb2_grpc.MarketDataServiceStub,       market_data_pb2.HealthRequest()),
        ('Order Executor via Nginx gRPC', 'localhost:9054', order_executor_pb2_grpc.OrderExecutorServiceStub, order_executor_pb2.HealthRequest()),
        ('Sentiment via Nginx gRPC',      'localhost:9053', sentiment_pb2_grpc.SentimentServiceStub,          sentiment_pb2.HealthRequest()),
        ('Chatbot via Nginx gRPC',        'localhost:9055', chatbot_pb2_grpc.ChatbotServiceStub,              chatbot_pb2.HealthRequest()),
    ]

    print("Testing gRPC through Nginx API Gateway:")
    print("=" * 50)
    for name, addr, stub_class, request in tests:
        try:
            channel = grpc.insecure_channel(addr)
            stub = stub_class(channel)
            response = stub.GetHealth(request, timeout=5)
            print(f'✓ {name}: {response.status} ({response.service})')
        except Exception as e:
            print(f'✗ {name}: FAILED - {str(e)[:100]}')

if __name__ == "__main__":
    test_all()