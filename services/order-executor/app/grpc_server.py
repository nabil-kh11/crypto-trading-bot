import grpc
from concurrent import futures
from app import order_executor_pb2
from app import order_executor_pb2_grpc
from app.executor import execute_trade
from app.database import get_all_trades
from app.binance_executor import get_testnet_balance

class OrderExecutorServicer(order_executor_pb2_grpc.OrderExecutorServiceServicer):

    def Execute(self, request, context):
        try:
            symbol = request.symbol.replace('-', '/').upper()
            result = execute_trade(symbol)
            return order_executor_pb2.ExecuteResponse(
                status=result.get('status', 'unknown'),
                signal=result.get('signal', ''),
                confidence=result.get('confidence', 0.0),
                model=result.get('model', ''),
                price=result.get('price', 0.0),
                message=result.get('reason', '')
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return order_executor_pb2.ExecuteResponse()

    def GetBalance(self, request, context):
        try:
            return order_executor_pb2.BalanceResponse(
                source='Binance Testnet',
                usdt=get_testnet_balance('USDT'),
                btc=get_testnet_balance('BTC'),
                eth=get_testnet_balance('ETH')
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return order_executor_pb2.BalanceResponse()

    def GetSignal(self, request, context):
        try:
            from app.executor import get_latest_candle, get_ml_signal, get_latest_price
            symbol = request.symbol.replace('-', '/').upper()
            candle = get_latest_candle(symbol)
            signal_data = get_ml_signal(symbol, candle)
            price = get_latest_price(symbol)
            return order_executor_pb2.SignalResponse(
                signal=signal_data['signal'],
                confidence=signal_data['confidence'],
                model=signal_data.get('model', ''),
                price=price
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return order_executor_pb2.SignalResponse()

    def GetTrades(self, request, context):
        try:
            trades = get_all_trades(
                symbol=request.symbol if request.symbol else None,
                limit=request.limit if request.limit else 50
            )
            trade_list = []
            for t in trades:
                trade_list.append(order_executor_pb2.Trade(
                    symbol=t.get('symbol', ''),
                    signal=t.get('signal', ''),
                    price=t.get('price', 0.0),
                    quantity=t.get('quantity', 0.0),
                    confidence=t.get('confidence', 0.0),
                    status=t.get('status', ''),
                    executed_at=str(t.get('executed_at', ''))
                ))
            return order_executor_pb2.TradesResponse(trades=trade_list)
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return order_executor_pb2.TradesResponse()

    def GetHealth(self, request, context):
        return order_executor_pb2.HealthResponse(
            status='ok',
            service='order-executor'
        )

def serve():
    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        order_executor_pb2_grpc.add_OrderExecutorServiceServicer_to_server(
            OrderExecutorServicer(), server
        )
        port = server.add_insecure_port('0.0.0.0:50054')
        print(f'[gRPC] Port binding result: {port}')
        server.start()
        print('[gRPC] Order Executor gRPC server started on port 50054')
        server.wait_for_termination()
    except Exception as e:
        print(f'[gRPC] ERROR: {e}')
        import traceback
        traceback.print_exc()