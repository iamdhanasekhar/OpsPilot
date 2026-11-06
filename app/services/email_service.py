import smtplib

from email.message import EmailMessage

from app.core.config import settings


class EmailService:

    @staticmethod
    def send_email(
        recipient: str,
        subject: str,
        body: str,
    ):
        if not settings.SMTP_EMAIL or not settings.SMTP_APP_PASSWORD:
            raise ValueError("SMTP credentials are not configured")

        message = EmailMessage()
        message["From"] = settings.SMTP_EMAIL
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            timeout=15,
        ) as smtp:

            smtp.starttls()
            smtp.login(
                settings.SMTP_EMAIL,
                settings.SMTP_APP_PASSWORD,
            )
            smtp.send_message(message)