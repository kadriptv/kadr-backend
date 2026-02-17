import os
import smtplib
from email.mime.text import MIMEText


SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)


def send_login_code(email: str, code: str):
    msg = MIMEText(f"Ваш код входа: {code}")
    msg["Subject"] = "IPTV Login Code"
    msg["From"] = SMTP_FROM
    msg["To"] = email

    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
        server.ehlo()
        server.starttls()
        server.ehlo()

        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, [email], msg.as_string())

        server.quit()

    except Exception as e:
        print("SMTP ERROR:", str(e))
        raise
