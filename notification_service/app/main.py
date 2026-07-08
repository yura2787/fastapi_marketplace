import json
import smtplib
import ssl
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pika
from settings import settings

SMTP_PORT = 465


def send_email(to_email: str, subject: str, html_body: str, text_body: str = ""):
    msg = MIMEMultipart("alternative")
    msg["From"] = f"ShopHub <{settings.USER}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    if text_body:
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(settings.SMTP_SERVER, SMTP_PORT, context=context) as server:
        server.login(settings.USER, settings.TOKEN_UKR_NET)
        server.sendmail(settings.USER, to_email, msg.as_string())


def build_verification_email(name: str, redirect_url: str) -> str:
    return f"""\
<!DOCTYPE html>
<html lang="uk">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background-color:#f1f5f9;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f1f5f9;padding:32px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0"
               style="max-width:600px;width:100%;background-color:#ffffff;border-radius:16px;overflow:hidden;
                      box-shadow:0 4px 24px rgba(15,23,42,0.08);font-family:Arial,Helvetica,sans-serif;">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#4f46e5 0%,#6366f1 100%);padding:36px 40px;text-align:center;">
              <div style="font-size:30px;font-weight:800;letter-spacing:-0.5px;color:#ffffff;">
                Shop<span style="color:#fbbf24;">Hub</span>
              </div>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:40px 40px 24px 40px;">
              <h1 style="margin:0 0 12px 0;font-size:24px;font-weight:700;color:#0f172a;">
                Вітаємо, {name}! 👋
              </h1>
              <p style="margin:0 0 24px 0;font-size:16px;line-height:1.6;color:#475569;">
                Дякуємо за реєстрацію в ShopHub. Залишився один крок — підтвердіть
                свою електронну адресу, натиснувши кнопку нижче.
              </p>

              <!-- Button -->
              <table role="presentation" cellpadding="0" cellspacing="0" style="margin:8px 0 28px 0;">
                <tr>
                  <td align="center" style="border-radius:10px;background:linear-gradient(135deg,#4f46e5 0%,#6366f1 100%);">
                    <a href="{redirect_url}" target="_blank"
                       style="display:inline-block;padding:15px 44px;font-size:16px;font-weight:700;
                              color:#ffffff;text-decoration:none;border-radius:10px;">
                      ✓ Підтвердити email
                    </a>
                  </td>
                </tr>
              </table>

              <p style="margin:0 0 8px 0;font-size:13px;color:#94a3b8;">
                Або скопіюйте це посилання у браузер:
              </p>
              <p style="margin:0;font-size:13px;word-break:break-all;">
                <a href="{redirect_url}" style="color:#6366f1;text-decoration:none;">{redirect_url}</a>
              </p>
            </td>
          </tr>

          <!-- Divider -->
          <tr>
            <td style="padding:0 40px;">
              <div style="border-top:1px solid #e2e8f0;"></div>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:24px 40px 36px 40px;">
              <p style="margin:0;font-size:13px;line-height:1.6;color:#94a3b8;">
                Якщо ви не реєструвалися в ShopHub, просто проігноруйте цей лист.
              </p>
              <p style="margin:16px 0 0 0;font-size:12px;color:#cbd5e1;">
                © 2026 ShopHub. Усі права захищено.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def handle_user_registration(body: dict):
    name = body.get("name", "User")
    email = body.get("email")
    redirect_url = body.get("redirect_url", "")

    html = build_verification_email(name, redirect_url)
    text = (
        f"Вітаємо, {name}!\n\n"
        f"Дякуємо за реєстрацію в ShopHub. Підтвердіть свою електронну адресу за посиланням:\n"
        f"{redirect_url}\n\n"
        f"Якщо ви не реєструвалися, проігноруйте цей лист.\n"
    )
    send_email(email, "Підтвердіть свою реєстрацію в ShopHub", html, text_body=text)
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
