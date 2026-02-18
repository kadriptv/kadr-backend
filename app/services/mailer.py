import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM")


def send_login_code(email: str, code: str):
    html = f"""
    <html>
    <body style="margin:0;padding:0;background:#0f172a;font-family:Arial, sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background:#111827;border-radius:12px;padding:30px;color:#fff;">
                        
                        <!-- LOGO -->
                        <tr>
                            <td align="center" style="font-size:26px;font-weight:bold;color:#22c55e;">
                                📺 KadrTV
                            </td>
                        </tr>

                        <!-- TITLE -->
                        <tr>
                            <td align="center" style="padding-top:20px;font-size:20px;">
                                Код входа в аккаунт
                            </td>
                        </tr>

                        <!-- DESCRIPTION -->
                        <tr>
                            <td align="center" style="padding-top:10px;font-size:14px;color:#9ca3af;">
                                Используйте этот код для входа в приложение
                            </td>
                        </tr>

                        <!-- CODE -->
                        <tr>
                            <td align="center" style="padding-top:30px;">
                                <div style="
                                    display:inline-block;
                                    padding:15px 30px;
                                    font-size:32px;
                                    letter-spacing:6px;
                                    background:#22c55e;
                                    color:#000;
                                    border-radius:10px;
                                    font-weight:bold;
                                ">
                                    {code}
                                </div>
                            </td>
                        </tr>

                        <!-- EXPIRE -->
                        <tr>
                            <td align="center" style="padding-top:20px;font-size:13px;color:#9ca3af;">
                                Код действителен 10 минут
                            </td>
                        </tr>

                        <!-- WARNING -->
                        <tr>
                            <td align="center" style="padding-top:20px;font-size:12px;color:#6b7280;">
                                Если вы не запрашивали код — просто проигнорируйте это письмо
                            </td>
                        </tr>

                        <!-- FOOTER -->
                        <tr>
                            <td align="center" style="padding-top:30px;font-size:12px;color:#4b5563;">
                                © KadrTV IPTV Service
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    message = Mail(
        from_email=EMAIL_FROM,
        to_emails=email,
        subject="Ваш код входа в KadrTV",
        html_content=html
    )

    sg = SendGridAPIClient(SENDGRID_API_KEY)
    sg.send(message)
