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
                    open=float(row.get('open', 0)),
                    high=float(row.get('high', 0)),
                    low=float(row.get('low', 0)),
                    close=float(row.get('close', 0)),
                    volume=float(row.get('volume', 0)),
                    rsi=float(row.get('rsi', 0)),
                    ma20=float(row.get('ma20', 0)),
                    ma50=float(row.get('ma50', 0)),
                    ma200=float(row.get('ma200', 0)),
                    returns=float(row.get('returns', 0)),
                    vol_20=float(row.get('vol_20', 0)),
                    macd=float(row.get('macd', 0)),
                    macd_signal=float(row.get('macd_signal', 0)),
                    macd_diff=float(row.get('macd_diff', 0)),
                    bb_high=float(row.get('bb_high', 0)),
                    bb_low=float(row.get('bb_low', 0)),
                    bb_mid=float(row.get('bb_mid', 0)),
                    bb_width=float(row.get('bb_width', 0)),
                    bb_pct=float(row.get('bb_pct', 0)),
                    atr=float(row.get('atr', 0)),
                    stoch_rsi=float(row.get('stoch_rsi', 0)),
                    stoch_rsi_k=float(row.get('stoch_rsi_k', 0)),
                    stoch_rsi_d=float(row.get('stoch_rsi_d', 0)),
                    volume_ratio=float(row.get('volume_ratio', 0)),
                    dist_ma200=float(row.get('dist_ma200', 0)),
                    dist_ma50=float(row.get('dist_ma50', 0)),
                    hour=float(row.get('hour', 0)),
                    day_of_week=float(row.get('day_of_week', 0)),
                    close_lag_1=float(row.get('close_lag_1', 0)),
                    returns_lag_1=float(row.get('returns_lag_1', 0)),
                    close_lag_2=float(row.get('close_lag_2', 0)),
                    returns_lag_2=float(row.get('returns_lag_2', 0)),
                    close_lag_3=float(row.get('close_lag_3', 0)),
                    returns_lag_3=float(row.get('returns_lag_3', 0)),
                    close_lag_6=float(row.get('close_lag_6', 0)),
                    returns_lag_6=float(row.get('returns_lag_6', 0)),
                    close_lag_12=float(row.get('close_lag_12', 0)),
                    returns_lag_12=float(row.get('returns_lag_12', 0)),
                    close_lag_24=float(row.get('close_lag_24', 0)),
                    returns_lag_24=float(row.get('returns_lag_24', 0)),
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