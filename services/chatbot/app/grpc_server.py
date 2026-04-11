import grpc
from concurrent import futures
from app import chatbot_pb2
from app import chatbot_pb2_grpc
from app.rag import answer_question

class ChatbotServicer(chatbot_pb2_grpc.ChatbotServiceServicer):

    def Ask(self, request, context):
        try:
            result = answer_question(request.question)
            return chatbot_pb2.AskResponse(
                answer=result.get('answer', ''),
                sources=result.get('sources', [])
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return chatbot_pb2.AskResponse()

    def GetHealth(self, request, context):
        return chatbot_pb2.HealthResponse(
            status='ok',
            service='chatbot'
        )

def serve():
    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        chatbot_pb2_grpc.add_ChatbotServiceServicer_to_server(
            ChatbotServicer(), server
        )
        port = server.add_insecure_port('0.0.0.0:50055')
        print(f'[gRPC] Port binding result: {port}')
        server.start()
        print('[gRPC] Chatbot gRPC server started on port 50055')
        server.wait_for_termination()
    except Exception as e:
        print(f'[gRPC] ERROR: {e}')
        import traceback
        traceback.print_exc()

