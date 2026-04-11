import grpc
from concurrent import futures
from app import sentiment_pb2
from app import sentiment_pb2_grpc
from app.database import get_sentiment_summary

class SentimentServicer(sentiment_pb2_grpc.SentimentServiceServicer):

    def GetSummary(self, request, context):
        try:
            summary = get_sentiment_summary(request.asset)
            return sentiment_pb2.SummaryResponse(
                asset=request.asset,
                total_posts=summary.get('total_posts', 0),
                positive=summary.get('positive', 0),
                negative=summary.get('negative', 0),
                neutral=summary.get('neutral', 0),
                avg_score=summary.get('avg_score', 0.0),
                label=summary.get('label', 'Neutral')
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return sentiment_pb2.SummaryResponse()

    def GetHealth(self, request, context):
        return sentiment_pb2.HealthResponse(
            status='ok',
            service='sentiment-collector'
        )

def serve():
    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        sentiment_pb2_grpc.add_SentimentServiceServicer_to_server(
            SentimentServicer(), server
        )
        port = server.add_insecure_port('0.0.0.0:50053')
        print(f'[gRPC] Port binding result: {port}')
        server.start()
        print('[gRPC] Sentiment Collector gRPC server started on port 50053')
        server.wait_for_termination()
    except Exception as e:
        print(f'[gRPC] ERROR: {e}')
        import traceback
        traceback.print_exc()