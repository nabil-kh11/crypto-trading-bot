import grpc
from concurrent import futures
import time
from app import ml_engine_pb2
from app import ml_engine_pb2_grpc
from app.predictor import predict

class MLEngineServicer(ml_engine_pb2_grpc.MLEngineServiceServicer):

    def Predict(self, request, context):
        try:
            features = dict(request.features)
            result = predict(request.symbol, features)
            return ml_engine_pb2.PredictResponse(
                symbol=request.symbol,
                signal=result['signal'],
                confidence=result['confidence'],
                model=result['model'],
                probabilities=result.get('probabilities', {})
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ml_engine_pb2.PredictResponse()

    def GetHealth(self, request, context):
        return ml_engine_pb2.HealthResponse(
            status='ok',
            service='ml-decision-engine'
        )

    def GetSymbols(self, request, context):
        return ml_engine_pb2.SymbolsResponse(
            symbols=['BTC/USDT', 'ETH/USDT']
        )

def serve():
    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        ml_engine_pb2_grpc.add_MLEngineServiceServicer_to_server(
            MLEngineServicer(), server
        )
        port = server.add_insecure_port('0.0.0.0:50052')
        print(f'[gRPC] Port binding result: {port}')
        server.start()
        print('[gRPC] ML Decision Engine gRPC server started on port 50052')
        server.wait_for_termination()
    except Exception as e:
        print(f'[gRPC] ERROR starting gRPC server: {e}')