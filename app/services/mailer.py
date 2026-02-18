import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

log = logging.getLogger("mailer")

SENDGRID_API_KEY = (os.getenv("SENDGRID_API_KEY") or "").strip()
EMAIL_FROM = (os.getenv("EMAIL_FROM") or "").strip()
EMAIL_FROM_NAME = (os.getenv("EMAIL_FROM_NAME") or "Kadr IPTV").strip()
EMAIL_REPLY_TO = (os.getenv("EMAIL_REPLY_TO") or "").strip()

APP_NAME = (os.getenv("APP_NAME") or "Kadr IPTV").strip()
SUPPORT_EMAIL = (os.getenv("SUPPORT_EMAIL") or EMAIL_FROM).strip()


def _must(v: str, name: str):
    if not v:
        raise RuntimeError(f"{name} is not set")
    return v


def send_login_code(email: str, code: str):
    """
    Premium email login code via SendGrid.
    В Render Logs будет статус отправки (202=OK) или причина ошибки.
    """

    api_key = _must(SENDGRID_API_KEY, "SENDGRID_API_KEY")
    from_addr = _must(EMAIL_FROM, "EMAIL_FROM")

    if "@" not in from_addr:
        raise RuntimeError(f"EMAIL_FROM must contain '@', got: {from_addr}")

    subject = f"Код входа в {APP_NAME}: {code}"

    # Важно для доставляемости: текстовая версия
    text = (
        f"{APP_NAME}\n\n"
        f"Здравствуйте!\n"
        f"Ваш код входа: {code}\n"
        f"Код действует 10 минут.\n\n"
        f"Если вы не запрашивали код — просто проигнорируйте это письмо.\n"
        f"Поддержка: {SUPPORT_EMAIL}\n"
    )

    # Premium HTML (табличная верстка + безопасные стили для почтовиков)
    html = f"""\
<!doctype html>
<html lang="ru">
  <head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <title>{APP_NAME} — код входа</title>
  </head>
  <body style="margin:0;padding:0;background:#0b1220;font-family:Arial,Helvetica,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#0b1220;padding:24px 12px;">
      <tr>
        <td align="center">

          <table width="600" cellpadding="0" cellspacing="0" border="0"
                 style="width:600px;max-width:600px;background:#0f1b33;border-radius:16px;overflow:hidden;border:1px solid rgba(255,255,255,0.08);">
            <!-- Header -->
            <tr>
              <td style="padding:18px 20px;background:linear-gradient(135deg,#142a55,#0f1b33);color:#ffffff;">
                <div style="font-size:18px;font-weight:700;line-height:1.2;">
                  📺 {APP_NAME}
                </div>
                <div style="margin-top:6px;font-size:13px;opacity:.85;line-height:1.4;">
                  IPTV сервис • быстрый вход • безопасно
                </div>
              </td>
            </tr>

            <!-- Body -->
            <tr>
              <td style="padding:22px 20px;color:#e9eefc;">
                <div style="font-size:20px;font-weight:700;margin:0 0 8px 0;">
                  Здравствуйте!
                </div>

                <div style="font-size:14px;opacity:.92;line-height:1.6;">
                  Спасибо, что выбираете <b>{APP_NAME}</b> 💙<br/>
                  Чтобы подтвердить вход, введите этот код в приложении:
                </div>

                <!-- Code block -->
                <table cellpadding="0" cellspacing="0" border="0" style="margin:18px 0 10px 0;">
                  <tr>
                    <td align="center"
                        style="background:#16a34a;color:#ffffff;font-weight:800;font-size:30px;letter-spacing:6px;
                               padding:14px 18px;border-radius:14px;">
                      {code}
                    </td>
                  </tr>
                </table>

                <div style="font-size:13px;opacity:.75;line-height:1.5;">
                  Код действует <b>10 минут</b>. Никому не сообщайте код.
                </div>

                <!-- Tip -->
                <div style="margin-top:14px;padding:12px 14px;border-radius:12px;background:rgba(255,255,255,0.06);
                            font-size:13px;opacity:.92;line-height:1.5;">
                  Совет: если письмо не пришло — проверьте папки <b>Спам</b> и <b>Промоакции</b>.
                </div>

                <!-- Security note -->
                <div style="margin-top:16px;font-size:12px;opacity:.7;line-height:1.5;">
                  Если вы не запрашивали это письмо — просто проигнорируйте его.
                  Никому не сообщайте код/скриншот.
                </div>
              </td>
            </tr>

            <!-- Footer -->
            <tr>
              <td style="padding:14px 20px;border-top:1px solid rgba(255,255,255,0.08);
                         color:rgba(255,255,255,0.55);font-size:12px;line-height:1.5;">
                Поддержка: {SUPPORT_EMAIL}<br/>
                © 2026 {APP_NAME}. Это автоматическое письмо, отвечать на него не нужно.
              </td>
            </tr>
          </table>

          <div style="max-width:600px;margin-top:10px;color:rgba(255,255,255,0.35);font-size:11px;line-height:1.4;">
            Если вы используете корпоративную почту, письма могут задерживаться фильтрами безопасности.
          </div>

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

    # Reply-To по желанию
    if EMAIL_REPLY_TO and "@" in EMAIL_REPLY_TO:
        message.reply_to = Email(EMAIL_REPLY_TO)

    # Отправка + лог
    sg = SendGridAPIClient(api_key)
    resp = sg.send(message)

    log.warning("SendGrid sent: status=%s to=%s", resp.status_code, email)

    # 202 = accepted
    if int(resp.status_code) >= 400:
        raise RuntimeError(f"SendGrid error: status={resp.status_code}, body={getattr(resp, 'body', b'')}")
