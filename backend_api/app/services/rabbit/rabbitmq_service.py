import json
import ssl

import aio_pika
from settings import settings


class RabbitMQBroker:
    async def send_message(self, message: dict, queue_name: str):
        ssl_context = ssl.create_default_context()
        connection = await aio_pika.connect_robust(
            host=settings.RMQ_HOST,
            port=settings.RMQ_PORT,
            virtualhost=settings.RMQ_VIRTUAL_HOST,
            login=settings.RMQ_USER,
            password=settings.RMQ_PASSWORD,
            ssl=True,
            ssl_context=ssl_context,
        )
        async with connection:
            channel = await connection.channel()
            await channel.declare_queue(queue_name, durable=True)
            await channel.default_exchange.publish(
                aio_pika.Message(body=json.dumps(message).encode()),
                routing_key=queue_name,
            )


rabbitmq_broker = RabbitMQBroker()
