import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM")


def send_login_code(email: str, code: str):
    if not SENDGRID_API_KEY:
        raise Exception("SENDGRID_API_KEY not set")

    message = Mail(
        from_email=EMAIL_FROM,
        to_emails=email,
        subject="Ваш код входа",
        html_content=f"<strong>Ваш код входа: {code}</strong>"
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        if response.status_code >= 400:
            raise Exception(f"SendGrid error: {response.status_code}")

    except Exception as e:
        raise Exception(f"SendGrid failed: {e}")
