import json
import smtplib
import ssl
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pika
from settings import settings

SMTP_PORT = 465


def send_email(to_email: str, subject: str, html_body: str):
    msg = MIMEMultipart("alternative")
    msg["From"] = settings.USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(settings.SMTP_SERVER, SMTP_PORT, context=context) as server:
        server.login(settings.USER, settings.TOKEN_UKR_NET)
        server.sendmail(settings.USER, to_email, msg.as_string())


def handle_user_registration(body: dict):
    name = body.get("name", "User")
    email = body.get("email")
    redirect_url = body.get("redirect_url", "")

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>Welcome, {name}!</h2>
        <p>Thank you for registering. Please verify your email address:</p>
        <a href="{redirect_url}"
           style="background:#4CAF50;color:white;padding:12px 24px;text-decoration:none;border-radius:4px;">
           Verify Email
        </a>
        <p style="color:#999;margin-top:24px;font-size:12px;">
            If you did not register, ignore this email.
        </p>
    </div>
    """
    send_email(email, "Verify your email", html)
    print(f"[OK] Verification email sent to {email}")


def on_message(ch, method, properties, body):
    try:
        data = json.loads(body)
        queue = method.routing_key

        if queue == "user_registration":
            handle_user_registration(data)

        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"[ERROR] Failed to process message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def get_connection() -> pika.BlockingConnection:
    ssl_context = ssl.create_default_context()
    return pika.BlockingConnection(
        pika.ConnectionParameters(
            host=settings.RMQ_HOST,
            port=settings.RMQ_PORT,
            virtual_host=settings.RMQ_VIRTUAL_HOST,
            credentials=pika.PlainCredentials(settings.RMQ_USER, settings.RMQ_PASSWORD),
            ssl_options=pika.SSLOptions(context=ssl_context),
        )
    )


def main():
    while True:
        try:
            connection = get_connection()
            channel = connection.channel()
            channel.queue_declare(queue="user_registration", durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue="user_registration", on_message_callback=on_message)
            print("[*] Notification service ready. Waiting for messages...")
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError as e:
            print(f"[WARN] RabbitMQ connection lost: {e}. Retrying in 5s...")
            time.sleep(5)
        except KeyboardInterrupt:
            print("Shutting down.")
            break


if __name__ == "__main__":
    main()
