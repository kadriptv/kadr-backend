import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To

log = logging.getLogger("mailer")

SENDGRID_API_KEY = (os.getenv("SENDGRID_API_KEY") or "").strip()
EMAIL_FROM = (os.getenv("EMAIL_FROM") or "").strip()
EMAIL_FROM_NAME = (os.getenv("EMAIL_FROM_NAME") or "Kadr IPTV").strip()
EMAIL_REPLY_TO = (os.getenv("EMAIL_REPLY_TO") or "").strip()

def _must(v: str, name: str):
    if not v:
        raise RuntimeError(f"{name} is not set")
    return v

def send_login_code(email: str, code: str):
    """
    Отправка кода входа через SendGrid.
    Если что-то не так — выбрасывает Exception, который ты увидишь в Render Logs.
    """

    api_key = _must(SENDGRID_API_KEY, "SENDGRID_API_KEY")
    from_addr = _must(EMAIL_FROM, "EMAIL_FROM")

    # Быстрая защита от ошибки типа "kadriptvgmail.com"
    if "@" not in from_addr:
        raise RuntimeError(f"EMAIL_FROM must contain '@', got: {from_addr}")

    subject = "Код входа в Kadr IPTV"

    html = f"""
    <div style="font-family:Arial,Helvetica,sans-serif;background:#0b1220;padding:24px;">
      <div style="max-width:560px;margin:0 auto;background:#0f1b33;border-radius:16px;overflow:hidden;border:1px solid rgba(255,255,255,0.08);">
        <div style="padding:18px 20px;background:linear-gradient(135deg,#142a55,#0f1b33);color:#fff;">
          <div style="font-size:18px;font-weight:700;">Kadr IPTV</div>
          <div style="opacity:.85;margin-top:6px;font-size:13px;">Быстрый вход • безопасно • 1 минуту</div>
        </div>

        <div style="padding:22px 20px;color:#e9eefc;">
          <div style="font-size:20px;font-weight:700;margin-bottom:8px;">Здравствуйте!</div>
          <div style="opacity:.9;line-height:1.5;">
            Спасибо, что выбираете <b>Kadr IPTV</b> 💙<br/>
            Чтобы подтвердить вход, введите этот код в приложении:
          </div>

          <div style="margin:18px 0 10px;display:inline-block;background:#16a34a;color:#fff;font-weight:800;font-size:28px;letter-spacing:3px;padding:12px 18px;border-radius:14px;">
            {code}
          </div>

          <div style="opacity:.75;font-size:13px;margin-top:6px;">
            Код действует <b>10 минут</b>. Никому не сообщайте код.
          </div>

          <div style="margin-top:14px;padding:12px 14px;border-radius:12px;background:rgba(255,255,255,0.06);opacity:.9;font-size:13px;line-height:1.45;">
            Если письмо не пришло — проверьте папки <b>Спам</b> и <b>Промоакции</b>.
          </div>

          <div style="margin-top:18px;opacity:.7;font-size:12px;line-height:1.4;">
            Если вы не запрашивали код — просто проигнорируйте это письмо.
          </div>
        </div>

        <div style="padding:14px 20px;color:rgba(255,255,255,0.55);font-size:12px;border-top:1px solid rgba(255,255,255,0.08);">
          Поддержка: {from_addr}<br/>
          © 2026 Kadr IPTV
        </div>
      </div>
    </div>
    """

    message = Mail(
        from_email=Email(from_addr, EMAIL_FROM_NAME),
        to_emails=To(email),
        subject=subject,
        html_content=html
    )

    if EMAIL_REPLY_TO:
        message.reply_to = Email(EMAIL_REPLY_TO)

    try:
        sg = SendGridAPIClient(api_key)
        resp = sg.send(message)
        log.warning("SendGrid sent: status=%s to=%s", resp.status_code, email)
        # 202 - accepted
        if int(resp.status_code) >= 400:
            raise RuntimeError(f"SendGrid error: status={resp.status_code} body={getattr(resp, 'body', b'')}")
    except Exception as e:
        log.exception("SendGrid send failed: %s", e)
        raise
