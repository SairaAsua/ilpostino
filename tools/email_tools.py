"""
Herramienta para enviar emails desde ilPostino via Gmail.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_site_ready_email(recipient_email: str, recipient_name: str, site_url: str) -> dict:
    """Envía email de confirmación cuando el sitio está publicado.

    Args:
        recipient_email: Email del cliente.
        recipient_name: Nombre del cliente.
        site_url: URL pública del sitio generado.

    Returns:
        dict con status y mensaje.
    """
    gmail_user = os.environ.get("GMAIL_USER", "")
    gmail_pass = os.environ.get("GMAIL_APP_PASSWORD", "")

    if not gmail_user or not gmail_pass:
        return {"status": "error", "detail": "Credenciales Gmail no configuradas"}

    html = f"""
    <div style="font-family: 'Georgia', serif; max-width: 600px; margin: 0 auto;
                padding: 48px 40px; background: #FDFBF7; color: #3D3835;">

      <p style="font-size: 13px; letter-spacing: 2px; text-transform: uppercase;
                color: #A0522D; margin-bottom: 32px;">ilPostino</p>

      <h1 style="font-size: 32px; font-weight: normal; margin: 0 0 16px;">
        Tu sitio está listo, {recipient_name.split()[0]} ✨
      </h1>

      <p style="font-size: 17px; line-height: 1.8; color: #5a5350; margin-bottom: 32px;">
        Nuestros agentes de IA construyeron tu web personal desde cero.
        Ya está publicado y accesible para el mundo.
      </p>

      <div style="text-align: center; margin: 40px 0;">
        <a href="{site_url}"
           style="background: #A0522D; color: white; padding: 18px 40px;
                  text-decoration: none; border-radius: 4px; font-size: 16px;
                  display: inline-block; letter-spacing: 0.5px;">
          Ver mi sitio web →
        </a>
      </div>

      <div style="background: #f5f0e6; border-radius: 8px; padding: 24px; margin: 32px 0;">
        <p style="font-size: 14px; color: #7a6f68; margin: 0 0 8px;">
          <strong>Tu URL personal:</strong>
        </p>
        <p style="font-size: 15px; color: #A0522D; margin: 0; word-break: break-all;">
          <a href="{site_url}" style="color: #A0522D;">{site_url}</a>
        </p>
      </div>

      <p style="font-size: 15px; line-height: 1.8; color: #5a5350;">
        Podés actualizar tu sitio en cualquier momento enviando un mensaje
        por <strong>Telegram</strong>. Fotos, novedades, proyectos nuevos —
        todo se refleja automáticamente en tu web.
      </p>

      <hr style="border: none; border-top: 1px solid #e8e0d5; margin: 40px 0;">

      <p style="font-size: 12px; color: #bbb; text-align: center; margin: 0;">
        ilPostino · Tu marca personal, viva y actualizable.<br>
        Respondé este email si necesitás ayuda.
      </p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🎉 Tu sitio web está publicado — {site_url}"
    msg["From"] = f"ilPostino <{gmail_user}>"
    msg["To"] = recipient_email
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_pass)
            server.sendmail(gmail_user, recipient_email, msg.as_string())
        return {"status": "sent", "to": recipient_email}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
