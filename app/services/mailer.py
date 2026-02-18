import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To

log = logging.getLogger("mailer")

SENDGRID_API_KEY = (os.getenv("SENDGRID_API_KEY") or "").strip()
EMAIL_FROM = (os.getenv("EMAIL_FROM") or "").strip()
EMAIL_FROM_NAME = (os.getenv("EMAIL_FROM_NAME") or "Kadr IPTV").strip()

APP_NAME = (os.getenv("APP_NAME") or "Kadr IPTV").strip()
SUPPORT_EMAIL = (os.getenv("SUPPORT_EMAIL") or EMAIL_FROM).strip()

# Deep link / universal link для кнопки
# Примеры:
#   kadriptv://login
#   https://kadriptv.app/login
APP_DEEPLINK = (os.getenv("APP_DEEPLINK") or "").strip()


def _must(v: str, name: str):
    if not v:
        raise RuntimeError(f"{name} is not set")
    return v


def send_login_code(email: str, code: str):
    api_key = _must(SENDGRID_API_KEY, "SENDGRID_API_KEY")
    from_addr = _must(EMAIL_FROM, "EMAIL_FROM")

    subject = f"Код входа в {APP_NAME}: {code}"

    # Plain text (важно для доставляемости)
    text = (
        f"{APP_NAME}\n\n"
        f"Здравствуйте!\n"
        f"Ваш код входа: {code}\n"
        f"Код действует 10 минут.\n\n"
        f"Если вы не запрашивали код — просто проигнорируйте это письмо.\n"
        f"Поддержка: {SUPPORT_EMAIL}\n"
    )

    # Кнопка: показываем только если задан APP_DEEPLINK
    button_html = ""
    if APP_DEEPLINK:
        button_html = f"""
        <tr>
          <td align="center" style="padding:18px 0 6px 0;">
            <a href="{APP_DEEPLINK}"
               style="
                 display:inline-block;
                 text-decoration:none;
                 background:linear-gradient(180deg,#2D7DFF,#1F63E6);
                 color:#ffffff;
                 font-weight:700;
                 font-size:14px;
                 padding:12px 18px;
                 border-radius:999px;
                 box-shadow:0 10px 24px rgba(31,99,230,0.28);
               ">
              Открыть приложение →
            </a>
          </td>
        </tr>
        <tr>
          <td align="center" style="font-size:12px;color:rgba(255,255,255,0.55);padding:0 20px 6px 20px;">
            Если кнопка не открывает приложение — просто введите код вручную.
          </td>
        </tr>
        """

    html = f"""\
<!doctype html>
<html lang="ru">
  <head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <title>{APP_NAME} — вход</title>
  </head>

  <body style="margin:0;padding:0;background:#0a1020;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0"
           style="background:#0a1020;padding:24px 12px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;">
      <tr>
        <td align="center">

          <!-- Card -->
          <table width="600" cellpadding="0" cellspacing="0" border="0"
                 style="width:600px;max-width:600px;border-radius:20px;overflow:hidden;
                        background: radial-gradient(1200px 400px at 50% -20%, rgba(45,125,255,0.35), rgba(10,16,32,0)) ,
                                   linear-gradient(180deg,#0f1b33,#0a1020);
                        border:1px solid rgba(255,255,255,0.08);
                        box-shadow:0 18px 60px rgba(0,0,0,0.45);">

            <!-- Top bar -->
            <tr>
              <td style="padding:16px 18px 0 18px;">
                <table width="100%" cellpadding="0" cellspacing="0" border="0">
                  <tr>
                    <td style="color:#ffffff;">
                      <div style="font-size:16px;font-weight:800;letter-spacing:0.2px;">
                        📺 {APP_NAME}
                      </div>
                      <div style="margin-top:6px;font-size:12px;color:rgba(255,255,255,0.62);">
                        IPTV сервис • быстрый вход • безопасно
                      </div>
                    </td>
                    <td align="right" style="color:rgba(255,255,255,0.55);font-size:12px;">
                      🔒 Secure Login
                    </td>
                  </tr>
                </table>
              </td>
            </tr>

            <!-- Content -->
            <tr>
              <td style="padding:18px 18px 6px 18px;color:#eaf0ff;">
                <div style="font-size:22px;font-weight:900;line-height:1.2;margin:0;">
                  Здравствуйте!
                </div>

                <div style="margin-top:10px;font-size:14px;line-height:1.7;color:rgba(255,255,255,0.80);">
                  Спасибо, что выбираете <b>{APP_NAME}</b> 💙<br/>
                  Чтобы подтвердить вход, введите этот код в приложении:
                </div>

                <!-- Code pill (CENTER!) -->
                <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:18px;">
                  <tr>
                    <td align="center">
                      <table cellpadding="0" cellspacing="0" border="0"
                             style="border-radius:16px;overflow:hidden;
                                    background:linear-gradient(180deg,#16a34a,#0f7a33);
                                    box-shadow:0 14px 40px rgba(22,163,74,0.22);">
                        <tr>
                          <td align="center"
                              style="
                                padding:16px 22px;
                                font-size:34px;
                                font-weight:900;
                                letter-spacing:8px;
                                color:#ffffff;
                                text-align:center;
                                white-space:nowrap;
                              ">
                            {code}
                          </td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                </table>

                <div style="margin-top:12px;font-size:12px;color:rgba(255,255,255,0.62);text-align:center;">
                  ⏱ Код действует <b>10 минут</b> • Никому не сообщайте код
                </div>

                {button_html}

                <div style="margin-top:14px;font-size:12px;color:rgba(255,255,255,0.55);line-height:1.6;">
                  Если вы не запрашивали это письмо — просто проигнорируйте его.
                  Никому не отправляйте код или скриншот.
                </div>
              </td>
            </tr>

            <!-- Footer -->
            <tr>
              <td style="padding:14px 18px;border-top:1px solid rgba(255,255,255,0.08);
                         color:rgba(255,255,255,0.55);font-size:12px;line-height:1.6;">
                <div>Поддержка: <a href="mailto:{SUPPORT_EMAIL}" style="color:#7bb5ff;text-decoration:none;">{SUPPORT_EMAIL}</a></div>
                <div style="margin-top:4px;">© 2026 {APP_NAME}. Это автоматическое письмо, отвечать на него не нужно.</div>
              </td>
            </tr>

          </table>
          <!-- /Card -->

        </td>
      </tr>
    </table>
  </body>
</html>
"""

    message = Mail(
        from_email=Email(from_addr, EMAIL_FROM_NAME),
        to_emails=To(email),
        subject=subject,
        plain_text_content=text,
        html_content=html,
    )

    sg = SendGridAPIClient(api_key)
    resp = sg.send(message)

    log.warning("SendGrid sent: status=%s to=%s", resp.status_code, email)
    if int(resp.status_code) >= 400:
        raise RuntimeError(f"SendGrid error: status={resp.status_code}, body={getattr(resp, 'body', b'')}")
