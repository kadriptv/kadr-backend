import os
from datetime import datetime, timezone
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


# ===== ENV =====
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "").strip()
EMAIL_FROM = os.getenv("EMAIL_FROM", "").strip()

BRAND_NAME = os.getenv("BRAND_NAME", "KadrTV").strip()
APP_URL = os.getenv("APP_URL", "https://kadr-backend-9lke.onrender.com/docs").strip()
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", EMAIL_FROM).strip()


# ===== INTERNAL: HTML WRAPPER =====
def _wrap_html(title: str, preheader: str, body_html: str) -> str:
    year = datetime.now(timezone.utc).year
    # NOTE: preheader is hidden preview text for email clients
    return f"""\
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{title}</title>
</head>
<body style="margin:0;padding:0;background:#0b1220;font-family:Arial,Helvetica,sans-serif;">
  <div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;">
    {preheader}
  </div>

  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0b1220;padding:24px 12px;">
    <tr>
      <td align="center">
        <table width="640" cellpadding="0" cellspacing="0"
               style="width:640px;max-width:640px;background:#0f172a;border-radius:16px;overflow:hidden;border:1px solid rgba(255,255,255,0.08);">
          <!-- Header -->
          <tr>
            <td style="padding:22px 24px;background:linear-gradient(135deg,#111827,#0f172a);border-bottom:1px solid rgba(255,255,255,0.08);">
              <div style="font-size:22px;font-weight:800;color:#22c55e;letter-spacing:0.2px;">
                📺 {BRAND_NAME}
              </div>
              <div style="margin-top:6px;font-size:12px;color:rgba(255,255,255,0.60);">
                IPTV сервис • быстрый вход • безопасно
              </div>
            </td>
          </tr>

          <!-- Content -->
          <tr>
            <td style="padding:26px 24px;color:#ffffff;">
              {body_html}
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:18px 24px;background:#0b1220;border-top:1px solid rgba(255,255,255,0.08);">
              <div style="font-size:12px;color:rgba(255,255,255,0.55);line-height:1.6;">
                Если вы не запрашивали это письмо — просто игнорируйте его. Никому не сообщайте код/ссылку.
                <br/>
                Поддержка: <a href="mailto:{SUPPORT_EMAIL}" style="color:#22c55e;text-decoration:none;">{SUPPORT_EMAIL}</a>
                <br/>
                © {year} {BRAND_NAME}
              </div>
            </td>
          </tr>

        </table>

        <div style="margin-top:10px;font-size:11px;color:rgba(255,255,255,0.35);">
          Это автоматическое письмо. Отвечать на него не нужно.
        </div>

      </td>
    </tr>
  </table>
</body>
</html>
"""


def _send_email(to_email: str, subject: str, html: str):
    if not SENDGRID_API_KEY:
        raise RuntimeError("SENDGRID_API_KEY is not set")
    if not EMAIL_FROM:
        raise RuntimeError("EMAIL_FROM is not set")

    msg = Mail(
        from_email=EMAIL_FROM,
        to_emails=to_email,
        subject=subject,
        html_content=html
    )
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    sg.send(msg)


# =====================================================================
# PUBLIC API: EMAIL TEMPLATES
# =====================================================================

def send_login_code(email: str, code: str, minutes_valid: int = 10):
    title = "Код входа"
    preheader = f"Ваш код входа: {code} (действителен {minutes_valid} минут)"
    body = f"""
      <div style="font-size:20px;font-weight:800;line-height:1.2;">
        Вход в {BRAND_NAME}
      </div>

      <div style="margin-top:10px;font-size:14px;color:rgba(255,255,255,0.75);line-height:1.7;">
        Введите этот код в приложении, чтобы подтвердить вход.
      </div>

      <div style="margin-top:22px;text-align:center;">
        <div style="
          display:inline-block;
          padding:14px 22px;
          border-radius:14px;
          background:#22c55e;
          color:#03120a;
          font-size:34px;
          font-weight:900;
          letter-spacing:8px;
        ">{code}</div>
        <div style="margin-top:10px;font-size:12px;color:rgba(255,255,255,0.60);">
          Код действителен <b>{minutes_valid} минут</b>
        </div>
      </div>

      <div style="margin-top:22px;padding:14px;border-radius:12px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);">
        <div style="font-size:13px;color:rgba(255,255,255,0.75);line-height:1.7;">
          <b>Совет:</b> если письмо не пришло — проверьте «Спам» и «Промоакции».
        </div>
      </div>
    """
    html = _wrap_html(title, preheader, body)
    _send_email(email, f"Ваш код входа в {BRAND_NAME}: {code}", html)


def send_welcome(email: str):
    title = "Добро пожаловать"
    preheader = f"Аккаунт {BRAND_NAME} создан. Осталось выбрать пакет и начать просмотр."
    body = f"""
      <div style="font-size:20px;font-weight:800;line-height:1.2;">
        Добро пожаловать в {BRAND_NAME} 👋
      </div>

      <div style="margin-top:10px;font-size:14px;color:rgba(255,255,255,0.75);line-height:1.7;">
        Ваш аккаунт готов. Теперь можно выбрать пакет и начать просмотр.
      </div>

      <div style="margin-top:18px;padding:16px;border-radius:14px;background:rgba(34,197,94,0.10);border:1px solid rgba(34,197,94,0.35);">
        <div style="font-size:14px;line-height:1.7;color:rgba(255,255,255,0.85);">
          ✅ Быстрый вход по коду <br/>
          ✅ Доступ с нескольких устройств (в пределах лимита) <br/>
          ✅ EPG и удобная навигация
        </div>
      </div>

      <div style="margin-top:20px;">
        <a href="{APP_URL}" style="
          display:inline-block;
          background:#22c55e;
          color:#03120a;
          padding:12px 16px;
          border-radius:12px;
          text-decoration:none;
          font-weight:800;
          font-size:14px;
        ">Открыть сервис</a>
      </div>
    """
    html = _wrap_html(title, preheader, body)
    _send_email(email, f"Добро пожаловать в {BRAND_NAME}", html)


def send_payment_success(email: str, package_name: str):
    title = "Оплата прошла"
    preheader = f"Пакет {package_name} активирован. Приятного просмотра!"
    body = f"""
      <div style="font-size:20px;font-weight:800;line-height:1.2;">
        Оплата подтверждена ✅
      </div>

      <div style="margin-top:10px;font-size:14px;color:rgba(255,255,255,0.75);line-height:1.7;">
        Ваш пакет <b>{package_name}</b> активирован. Можно заходить в приложение и смотреть каналы.
      </div>

      <div style="margin-top:18px;padding:16px;border-radius:14px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);">
        <div style="font-size:14px;line-height:1.7;color:rgba(255,255,255,0.80);">
          Если входите на новом устройстве — используйте вход по коду (email → код → подтверждение).
        </div>
      </div>

      <div style="margin-top:20px;">
        <a href="{APP_URL}" style="
          display:inline-block;
          background:#22c55e;
          color:#03120a;
          padding:12px 16px;
          border-radius:12px;
          text-decoration:none;
          font-weight:800;
          font-size:14px;
        ">Перейти в {BRAND_NAME}</a>
      </div>
    """
    html = _wrap_html(title, preheader, body)
    _send_email(email, f"{BRAND_NAME}: пакет «{package_name}» активирован", html)


def send_subscription_expiring(email: str, days_left: int):
    title = "Подписка заканчивается"
    preheader = f"До окончания подписки осталось {days_left} дн."
    body = f"""
      <div style="font-size:20px;font-weight:800;line-height:1.2;">
        Подписка скоро закончится ⏳
      </div>

      <div style="margin-top:10px;font-size:14px;color:rgba(255,255,255,0.75);line-height:1.7;">
        До окончания подписки осталось: <b>{days_left} дн.</b><br/>
        Чтобы доступ к IPTV не прерывался — продлите пакет заранее.
      </div>

      <div style="margin-top:20px;">
        <a href="{APP_URL}" style="
          display:inline-block;
          background:#22c55e;
          color:#03120a;
          padding:12px 16px;
          border-radius:12px;
          text-decoration:none;
          font-weight:800;
          font-size:14px;
        ">Продлить подписку</a>
      </div>

      <div style="margin-top:16px;font-size:12px;color:rgba(255,255,255,0.55);line-height:1.7;">
        Если вы уже оплатили — просто проигнорируйте письмо.
      </div>
    """
    html = _wrap_html(title, preheader, body)
    _send_email(email, f"{BRAND_NAME}: подписка заканчивается через {days_left} дн.", html)
