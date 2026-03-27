import pika
import json
from app.config import RABBITMQ_URL, QUEUE_NAME

def publish_signal(signal_data: dict):
    try:
        params = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()

        channel.queue_declare(queue=QUEUE_NAME, durable=True)

        channel.basic_publish(
            exchange='',
            routing_key=QUEUE_NAME,
            body=json.dumps(signal_data),
            properties=pika.BasicProperties(
                delivery_mode=2  # make message persistent
            )
        )

        connection.close()
        print(f"Published signal to queue: {signal_data}")
        return True

    except Exception as e:
        print(f"Failed to publish to RabbitMQ: {e}")
        return False