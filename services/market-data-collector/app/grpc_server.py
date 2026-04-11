import grpc
from concurrent import futures
from app import market_data_pb2
from app import market_data_pb2_grpc
from app.collector import fetch_ohlcv, get_latest_price

class MarketDataServicer(market_data_pb2_grpc.MarketDataServiceServicer):

    def GetPrice(self, request, context):
        try:
            symbol = request.symbol.replace('-', '/')
            data = get_latest_price(symbol)
            return market_data_pb2.PriceResponse(
                symbol=symbol,
                price=data['price'],
                high=data.get('high', 0.0),
                low=data.get('low', 0.0),
                volume=data.get('volume', 0.0),
                timestamp=data.get('timestamp', '')
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return market_data_pb2.PriceResponse()

    def GetOHLCV(self, request, context):
        try:
            symbol = request.symbol.replace('-', '/')
            limit = request.limit if request.limit else 100
            df = fetch_ohlcv(symbol, limit=limit)
            candles = []
            for _, row in df.iterrows():
                candles.append(market_data_pb2.Candle(
                    timestamp=str(row['timestamp']),
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=float(row['volume']),
                    rsi=float(row.get('rsi', 0)),
                    ma20=float(row.get('ma20', 0)),
                    ma50=float(row.get('ma50', 0))
                ))
            return market_data_pb2.OHLCVResponse(candles=candles)
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return market_data_pb2.OHLCVResponse()

    def GetHealth(self, request, context):
        return market_data_pb2.HealthResponse(
            status='ok',
            service='market-data-collector'
        )

def serve():
    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        market_data_pb2_grpc.add_MarketDataServiceServicer_to_server(
            MarketDataServicer(), server
        )
        port = server.add_insecure_port('0.0.0.0:50051')
        print(f'[gRPC] Port binding result: {port}')
        server.start()
        print('[gRPC] Market Data Collector gRPC server started on port 50051')
        server.wait_for_termination()
    except Exception as e:
        print(f'[gRPC] ERROR: {e}')
        import traceback
        traceback.print_exc()