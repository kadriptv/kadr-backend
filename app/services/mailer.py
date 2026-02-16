import os
import smtplib
from email.mime.text import MIMEText

def send_login_code(to_email: str, code: str):
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASS", "")
    sender = os.getenv("SMTP_FROM", user)

    if not user or not password:
        raise RuntimeError("SMTP_USER/SMTP_PASS not configured")

    subject = os.getenv("SMTP_SUBJECT", "KadrTV: код входа")
    body = f"Ваш код входа: {code}\n\nКод действует 10 минут.\nЕсли это были не вы — просто игнорируйте письмо."

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email

    with smtplib.SMTP(host, port) as s:
        s.starttls()
        s.login(user, password)
        s.send_message(msg)
