import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from typing import Optional

import requests


# ===== Brand / Defaults =====
BRAND_NAME = (os.getenv("BRAND_NAME", "Kadr IPTV") or "Kadr IPTV").strip()
SUPPORT_EMAIL = (os.getenv("SUPPORT_EMAIL") or os.getenv("EMAIL_FROM") or "support@example.com").strip()

EMAIL_FROM = (os.getenv("EMAIL_FROM") or os.getenv("SMTP_USER") or "no-reply@example.com").strip()
EMAIL_FROM_NAME = (os.getenv("EMAIL_FROM_NAME") or BRAND_NAME).strip()

# ===== SendGrid (preferred in production) =====
SENDGRID_API_KEY = (os.getenv("SENDGRID_API_KEY") or "").strip()

# ===== SMTP fallback (Gmail App Password) =====
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = (os.getenv("SMTP_USER") or "").strip()
SMTP_PASSWORD = (os.getenv("SMTP_PASSWORD") or "").strip()


def _safe_mask_email(email: str) -> str:
    try:
        local, dom = email.split("@", 1)
        if len(local) <= 2:
            masked = local[:1] + "***"
        else:
            masked = local[:1] + "***" + local[-1:]
        return f"{masked}@{dom}"
    except Exception:
        return email


def _build_html_login_code(code: str, to_email: str, minutes_valid: int, greeting_name: Optional[str] = None) -> str:
    hello = f"Здравствуйте, {greeting_name.strip()} 👋" if greeting_name and greeting_name.strip() else "Здравствуйте! 👋"
    masked_email = _safe_mask_email(to_email)
    preheader = f"Код входа: {code}. Действителен {minutes_valid} минут."

    return f"""\
<!doctype html>
<html lang="ru">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{BRAND_NAME} — вход</title>
  </head>
  <body style="margin:0;padding:0;background:#0b1220;font-family:Arial,Helvetica,sans-serif;">
    <div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;">
      {preheader}
    </div>

    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background:#0b1220;padding:24px 12px;">
      <tr>
        <td align="center">
          <table role="presentation" cellpadding="0" cellspacing="0" width="620" style="max-width:620px;width:100%;">
            <tr>
              <td style="padding:10px 6px 18px 6px;">
                <div style="display:flex;align-items:center;gap:10px;">
                  <div style="width:40px;height:40px;border-radius:12px;background:linear-gradient(135deg,#22c55e,#16a34a);display:inline-block;"></div>
                  <div>
                    <div style="color:#e5e7eb;font-size:18px;font-weight:800;line-height:1;">{BRAND_NAME}</div>
                    <div style="color:rgba(229,231,235,0.7);font-size:12px;margin-top:4px;">IPTV сервис • быстрый вход • безопасно</div>
                  </div>
                </div>
              </td>
            </tr>

            <tr>
              <td style="
                background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.08);
                border-radius:18px;
                padding:26px 22px;
              ">
                <div style="color:#e5e7eb;font-size:22px;font-weight:900;line-height:1.25;">
                  Вход в {BRAND_NAME}
                </div>

                <div style="margin-top:14px;color:rgba(229,231,235,0.88);font-size:15px;line-height:1.75;">
                  {hello}<br/>
                  Спасибо, что выбираете <b>{BRAND_NAME}</b> 💚<br/>
                  Для подтверждения входа введите этот код в приложении:
                </div>

                <div style="margin-top:22px;text-align:center;">
                  <div style="
                    display:inline-block;
                    padding:16px 26px;
                    border-radius:16px;
                    background:linear-gradient(135deg,#22c55e,#16a34a);
                    color:#04130b;
                    font-size:38px;
                    font-weight:900;
                    letter-spacing:10px;
                    box-shadow:0 12px 34px rgba(34,197,94,0.35);
                  ">{code}</div>

                  <div style="margin-top:12px;color:rgba(229,231,235,0.65);font-size:13px;">
                    Код действителен <b>{minutes_valid} минут</b>
                  </div>

                  <div style="margin-top:8px;color:rgba(229,231,235,0.55);font-size:12px;">
                    Запрос выполнен для: <b>{masked_email}</b>
                  </div>
                </div>

                <div style="margin-top:22px;padding:14px 14px;border-radius:14px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);">
                  <div style="color:rgba(229,231,235,0.82);font-size:14px;line-height:1.65;">
                    💡 <b>Подсказка:</b> если письмо не пришло — проверьте папки <b>Спам</b> и <b>Промоакции</b>.
                  </div>
                </div>

                <div style="margin-top:12px;padding:14px 14px;border-radius:14px;background:rgba(34,197,94,0.10);border:1px solid rgba(34,197,94,0.25);">
                  <div style="color:rgba(229,231,235,0.88);font-size:14px;line-height:1.65;">
                    🔒 Мы заботимся о вашей безопасности.<br/>
                    Никому не сообщайте этот код — даже сотрудникам поддержки.
                  </div>
                </div>

                <div style="margin-top:18px;color:rgba(229,231,235,0.78);font-size:14px;line-height:1.7;">
                  Если вы не запрашивали вход — просто проигнорируйте это письмо.
                </div>

                <div style="margin-top:16px;color:rgba(229,231,235,0.88);font-size:14px;line-height:1.7;">
                  С уважением,<br/>
                  команда <b>{BRAND_NAME}</b>
                </div>

                <div style="margin-top:18px;color:rgba(229,231,235,0.55);font-size:12px;line-height:1.6;">
                  Поддержка: <span style="color:rgba(229,231,235,0.8);">{SUPPORT_EMAIL}</span><br/>
                  Это автоматическое письмо — отвечать на него не нужно.
                </div>
              </td>
            </tr>

            <tr>
              <td style="padding:16px 6px 0 6px;color:rgba(229,231,235,0.45);font-size:12px;text-align:center;">
                © {BRAND_NAME} — все права защищены
              </td>
            </tr>

          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""


def _build_text_login_code(code: str, minutes_valid: int) -> str:
    return (
        f"{BRAND_NAME}\n\n"
        f"Ваш код входа: {code}\n"
        f"Код действителен {minutes_valid} минут.\n\n"
        f"Если вы не запрашивали вход — просто проигнорируйте это письмо.\n"
        f"Поддержка: {SUPPORT_EMAIL}\n"
    )


def _send_via_sendgrid(to_email: str, subject: str, html: str, text: str) -> None:
    if not SENDGRID_API_KEY:
        raise RuntimeError("SENDGRID_API_KEY is not set")

    # IMPORTANT: EMAIL_FROM must be verified in SendGrid (Single Sender or Domain Authentication)
    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": EMAIL_FROM, "name": EMAIL_FROM_NAME},
        "subject": subject,
        "content": [
            {"type": "text/plain", "value": text},
            {"type": "text/html", "value": html},
        ],
    }

    r = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=20,
    )

    # SendGrid returns 202 Accepted on success
    if r.status_code != 202:
        raise RuntimeError(f"SendGrid error {r.status_code}: {r.text}")


def _send_via_smtp(to_email: str, subject: str, html: str, text: str) -> None:
    if not SMTP_USER or not SMTP_PASSWORD:
        raise RuntimeError("SMTP_USER/SMTP_PASSWORD are not set")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr((EMAIL_FROM_NAME, EMAIL_FROM))
    msg["To"] = to_email
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


def send_login_code(email: str, code: str, minutes_valid: int = 10, greeting_name: Optional[str] = None) -> None:
    subject = f"{BRAND_NAME}: код входа {code}"
    html = _build_html_login_code(code=code, to_email=email, minutes_valid=minutes_valid, greeting_name=greeting_name)
    text = _build_text_login_code(code=code, minutes_valid=minutes_valid)

    # Prefer SendGrid in production if configured
    if SENDGRID_API_KEY:
        _send_via_sendgrid(to_email=email, subject=subject, html=html, text=text)
        return

    # Fallback to SMTP
    _send_via_smtp(to_email=email, subject=subject, html=html, text=text)    code: str,
    to_email: str,
    minutes_valid: int,
    greeting_name: Optional[str] = None,
) -> str:
    # Greeting
    if greeting_name and greeting_name.strip():
        hello = f"Здравствуйте, {greeting_name.strip()} 👋"
    else:
        hello = "Здравствуйте! 👋"

    masked_email = _safe_mask_email(to_email)

    # Preheader (hidden preview text)
    preheader = f"Код входа: {code}. Действителен {minutes_valid} минут."

    return f"""\
<!doctype html>
<html lang="ru">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{BRAND_NAME} — вход</title>
  </head>
  <body style="margin:0;padding:0;background:#0b1220;font-family:Arial,Helvetica,sans-serif;">
    <div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;">
      {preheader}
    </div>

    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background:#0b1220;padding:24px 12px;">
      <tr>
        <td align="center">
          <table role="presentation" cellpadding="0" cellspacing="0" width="620" style="max-width:620px;width:100%;">
            <tr>
              <td style="padding:10px 6px 18px 6px;">
                <div style="display:flex;align-items:center;gap:10px;">
                  <div style="width:40px;height:40px;border-radius:12px;background:linear-gradient(135deg,#22c55e,#16a34a);display:inline-block;"></div>
                  <div>
                    <div style="color:#e5e7eb;font-size:18px;font-weight:800;line-height:1;">{BRAND_NAME}</div>
                    <div style="color:rgba(229,231,235,0.7);font-size:12px;margin-top:4px;">IPTV сервис • быстрый вход • безопасно</div>
                  </div>
                </div>
              </td>
            </tr>

            <tr>
              <td style="
                background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.08);
                border-radius:18px;
                padding:26px 22px;
              ">
                <div style="color:#e5e7eb;font-size:22px;font-weight:900;line-height:1.25;">
                  Вход в {BRAND_NAME}
                </div>

                <div style="margin-top:14px;color:rgba(229,231,235,0.88);font-size:15px;line-height:1.75;">
                  {hello}<br/>
                  Спасибо, что выбираете <b>{BRAND_NAME}</b> 💚<br/>
                  Для подтверждения входа введите этот код в приложении:
                </div>

                <div style="margin-top:22px;text-align:center;">
                  <div style="
                    display:inline-block;
                    padding:16px 26px;
                    border-radius:16px;
                    background:linear-gradient(135deg,#22c55e,#16a34a);
                    color:#04130b;
                    font-size:38px;
                    font-weight:900;
                    letter-spacing:10px;
                    box-shadow:0 12px 34px rgba(34,197,94,0.35);
                  ">{code}</div>

                  <div style="margin-top:12px;color:rgba(229,231,235,0.65);font-size:13px;">
                    Код действителен <b>{minutes_valid} минут</b>
                  </div>

                  <div style="margin-top:8px;color:rgba(229,231,235,0.55);font-size:12px;">
                    Запрос выполнен для: <b>{masked_email}</b>
                  </div>
                </div>

                <div style="margin-top:22px;padding:14px 14px;border-radius:14px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);">
                  <div style="color:rgba(229,231,235,0.82);font-size:14px;line-height:1.65;">
                    💡 <b>Подсказка:</b> если письмо не пришло — проверьте папки <b>Спам</b> и <b>Промоакции</b>.
                  </div>
                </div>

                <div style="margin-top:12px;padding:14px 14px;border-radius:14px;background:rgba(34,197,94,0.10);border:1px solid rgba(34,197,94,0.25);">
                  <div style="color:rgba(229,231,235,0.88);font-size:14px;line-height:1.65;">
                    🔒 Мы заботимся о вашей безопасности.<br/>
                    Никому не сообщайте этот код — даже сотрудникам поддержки.
                  </div>
                </div>

                <div style="margin-top:18px;color:rgba(229,231,235,0.78);font-size:14px;line-height:1.7;">
                  Если вы не запрашивали вход — просто проигнорируйте это письмо.
                </div>

                <div style="margin-top:16px;color:rgba(229,231,235,0.88);font-size:14px;line-height:1.7;">
                  С уважением,<br/>
                  команда <b>{BRAND_NAME}</b>
                </div>

                <div style="margin-top:18px;color:rgba(229,231,235,0.55);font-size:12px;line-height:1.6;">
                  Поддержка: <span style="color:rgba(229,231,235,0.8);">{SUPPORT_EMAIL}</span><br/>
                  Это автоматическое письмо — отвечать на него не нужно.
                </div>
              </td>
            </tr>

            <tr>
              <td style="padding:16px 6px 0 6px;color:rgba(229,231,235,0.45);font-size:12px;text-align:center;">
                © {BRAND_NAME} — все права защищены
              </td>
            </tr>

          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""


def _build_text_login_code(code: str, minutes_valid: int) -> str:
    return (
        f"{BRAND_NAME}\n\n"
        f"Ваш код входа: {code}\n"
        f"Код действителен {minutes_valid} минут.\n\n"
        f"Если вы не запрашивали вход — просто проигнорируйте это письмо.\n"
        f"Поддержка: {SUPPORT_EMAIL}\n"
    )


def _send_smtp(to_email: str, subject: str, html: str, text: str) -> None:
    if not SMTP_USER or not SMTP_PASSWORD:
        raise RuntimeError("SMTP_USER/SMTP_PASSWORD are not set")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr((EMAIL_FROM_NAME, EMAIL_FROM))
    msg["To"] = to_email
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


def send_login_code(email: str, code: str, minutes_valid: int = 10, greeting_name: Optional[str] = None) -> None:
    """
    Sends one-time login code email.
    Uses SMTP credentials from env:
      SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM, EMAIL_FROM_NAME
    """
    subject = f"{BRAND_NAME}: код входа {code}"
    html = _build_html_login_code(code=code, to_email=email, minutes_valid=minutes_valid, greeting_name=greeting_name)
    text = _build_text_login_code(code=code, minutes_valid=minutes_valid)
    _send_smtp(to_email=email, subject=subject, html=html, text=text)
