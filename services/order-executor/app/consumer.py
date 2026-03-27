import pika
import json
import threading
from app.config import RABBITMQ_URL, QUEUE_NAME
from app.executor import execute_trade

def on_message(channel, method, properties, body):
    try:
        signal_data = json.loads(body)
        symbol = signal_data.get('symbol', 'BTC/USDT')
        print(f"Received signal from queue: {signal_data}")
        result = execute_trade(symbol)
        print(f"Trade result: {result}")
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error processing message: {e}")
        channel.basic_nack(delivery_tag=method.delivery_tag)

def start_consumer():
    try:
        params = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue=QUEUE_NAME,
            on_message_callback=on_message
        )
        print(f"Listening for signals on queue: {QUEUE_NAME}")
        channel.start_consuming()
    except Exception as e:
        print(f"RabbitMQ consumer error: {e}")

def start_consumer_thread():
    thread = threading.Thread(target=start_consumer, daemon=True)
    thread.start()
    print("RabbitMQ consumer thread started!")