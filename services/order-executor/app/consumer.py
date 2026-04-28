import pika
import json
import threading
from datetime import datetime
from app.config import RABBITMQ_URL, QUEUE_NAME
from app.executor import execute_trade

def on_message(channel, method, properties, body):
    try:
        signal_data = json.loads(body)
        
        # Check if signal is too old (more than 2 minutes)
        timestamp_str = signal_data.get('timestamp')
        if timestamp_str:
            signal_time = datetime.fromisoformat(timestamp_str)
            age_seconds = (datetime.utcnow() - signal_time).total_seconds()
            if age_seconds > 120:  # 2 minutes
                print(f"[Consumer] Skipping stale signal ({age_seconds:.0f}s old): {signal_data}")
                channel.basic_ack(delivery_tag=method.delivery_tag)
                return

        symbol     = signal_data.get('symbol', 'BTC/USDT')
        signal     = signal_data.get('signal')
        confidence = signal_data.get('confidence')
        model      = signal_data.get('model', 'Unknown')
        print(f"Received signal from queue: {signal_data}")
        result = execute_trade(symbol, signal, confidence, model)
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