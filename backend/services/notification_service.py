"""
GrokDent FL — Notification Service
Sends appointment confirmations and reminders via Twilio SMS and SendGrid email.
Supports English and Spanish templates.  Falls back to logging when
Twilio / SendGrid credentials are not configured.
"""

import logging
from typing import Optional

from backend.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional Twilio / SendGrid imports
# ---------------------------------------------------------------------------
_twilio_client = None
_sendgrid_client = None

try:
    from twilio.rest import Client as TwilioClient

    if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
        _twilio_client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        logger.info("Twilio client initialised.")
    else:
        logger.info("Twilio credentials not set — SMS will be logged only.")
except ImportError:
    logger.info("Twilio library not installed — SMS will be logged only.")

try:
    import sendgrid
    from sendgrid.helpers.mail import Mail, Email, To, Content

    if settings.SENDGRID_API_KEY:
        _sendgrid_client = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        logger.info("SendGrid client initialised.")
    else:
        logger.info("SendGrid API key not set — email will be logged only.")
except ImportError:
    logger.info("SendGrid library not installed — email will be logged only.")


# ---------------------------------------------------------------------------
# Message templates
# ---------------------------------------------------------------------------
SMS_CONFIRMATION_EN = (
    "✅ {clinic_name}: Hi {patient_name}! Your {service} appointment is confirmed "
    "for {datetime}. Reply CONFIRM to confirm or call us to reschedule. "
    "We look forward to seeing you!"
)

SMS_CONFIRMATION_ES = (
    "✅ {clinic_name}: ¡Hola {patient_name}! Su cita de {service} está confirmada "
    "para el {datetime}. Responda CONFIRMAR para confirmar o llámenos para reprogramar. "
    "¡Esperamos verle pronto!"
)

SMS_REMINDER_EN = (
    "🦷 {clinic_name}: Reminder — {patient_name}, you have an appointment "
    "on {datetime}. Please arrive 10 minutes early. "
    "Reply C to confirm or R to reschedule."
)

SMS_REMINDER_ES = (
    "🦷 {clinic_name}: Recordatorio — {patient_name}, tiene una cita "
    "el {datetime}. Por favor llegue 10 minutos antes. "
    "Responda C para confirmar o R para reprogramar."
)

EMAIL_CONFIRMATION_SUBJECT_EN = "Appointment Confirmed — {clinic_name}"
EMAIL_CONFIRMATION_SUBJECT_ES = "Cita Confirmada — {clinic_name}"

EMAIL_CONFIRMATION_BODY_EN = """
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: #0ea5e9; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
        <h1 style="margin: 0;">🦷 {clinic_name}</h1>
        <p style="margin: 5px 0 0;">Your Appointment is Confirmed!</p>
    </div>
    <div style="padding: 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
        <p>Dear <strong>{patient_name}</strong>,</p>
        <p>Your dental appointment has been scheduled:</p>
        <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
            <tr><td style="padding: 8px; border-bottom: 1px solid #e5e7eb; font-weight: bold;">Service</td>
                <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{service}</td></tr>
            <tr><td style="padding: 8px; border-bottom: 1px solid #e5e7eb; font-weight: bold;">Date &amp; Time</td>
                <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{datetime}</td></tr>
        </table>
        <p><strong>Please remember:</strong></p>
        <ul>
            <li>Arrive 10 minutes before your appointment</li>
            <li>Bring your insurance card and photo ID</li>
            <li>Let us know if you need to cancel (24-hour notice required)</li>
        </ul>
        <p>If you need to reschedule, please call us or reply to this email.</p>
        <p style="color: #6b7280; font-size: 12px; margin-top: 30px;">
            This message was sent by GrokDent FL AI Receptionist on behalf of {clinic_name}.<br>
            Please do not reply directly to this automated email.
        </p>
    </div>
</body>
</html>
"""

EMAIL_CONFIRMATION_BODY_ES = """
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: #0ea5e9; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
        <h1 style="margin: 0;">🦷 {clinic_name}</h1>
        <p style="margin: 5px 0 0;">¡Su Cita está Confirmada!</p>
    </div>
    <div style="padding: 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
        <p>Estimado/a <strong>{patient_name}</strong>,</p>
        <p>Su cita dental ha sido programada:</p>
        <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
            <tr><td style="padding: 8px; border-bottom: 1px solid #e5e7eb; font-weight: bold;">Servicio</td>
                <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{service}</td></tr>
            <tr><td style="padding: 8px; border-bottom: 1px solid #e5e7eb; font-weight: bold;">Fecha y Hora</td>
                <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{datetime}</td></tr>
        </table>
        <p><strong>Por favor recuerde:</strong></p>
        <ul>
            <li>Llegar 10 minutos antes de su cita</li>
            <li>Traer su tarjeta de seguro y una identificación con foto</li>
            <li>Avísenos si necesita cancelar (se requiere 24 horas de anticipación)</li>
        </ul>
        <p>Si necesita reprogramar, por favor llámenos o responda a este correo.</p>
        <p style="color: #6b7280; font-size: 12px; margin-top: 30px;">
            Este mensaje fue enviado por GrokDent FL AI Receptionist en nombre de {clinic_name}.<br>
            Por favor no responda directamente a este correo automático.
        </p>
    </div>
</body>
</html>
"""


class NotificationService:
    """
    Sends appointment confirmations and reminders via SMS (Twilio) and
    email (SendGrid).  All methods fall back to logger output when
    external services are not configured.
    """

    # ------------------------------------------------------------------
    # SMS notifications
    # ------------------------------------------------------------------
    @staticmethod
    def send_appointment_confirmation_sms(
        phone: str,
        clinic_name: str,
        patient_name: str,
        datetime_str: str,
        service: str,
        language: str = "en",
    ) -> bool:
        """Send an appointment confirmation SMS.  Returns True on success."""
        template = SMS_CONFIRMATION_ES if language == "es" else SMS_CONFIRMATION_EN
        body = template.format(
            clinic_name=clinic_name,
            patient_name=patient_name,
            service=service,
            datetime=datetime_str,
        )
        return NotificationService._send_sms(phone, body)

    @staticmethod
    def send_reminder_sms(
        phone: str,
        clinic_name: str,
        patient_name: str,
        datetime_str: str,
        language: str = "en",
    ) -> bool:
        """Send an appointment reminder SMS.  Returns True on success."""
        template = SMS_REMINDER_ES if language == "es" else SMS_REMINDER_EN
        body = template.format(
            clinic_name=clinic_name,
            patient_name=patient_name,
            datetime=datetime_str,
        )
        return NotificationService._send_sms(phone, body)

    # ------------------------------------------------------------------
    # Email notifications
    # ------------------------------------------------------------------
    @staticmethod
    def send_confirmation_email(
        email: str,
        clinic_name: str,
        patient_name: str,
        datetime_str: str,
        service: str,
        language: str = "en",
    ) -> bool:
        """Send an appointment confirmation email.  Returns True on success."""
        if language == "es":
            subject = EMAIL_CONFIRMATION_SUBJECT_ES.format(clinic_name=clinic_name)
            html_body = EMAIL_CONFIRMATION_BODY_ES.format(
                clinic_name=clinic_name,
                patient_name=patient_name,
                service=service,
                datetime=datetime_str,
            )
        else:
            subject = EMAIL_CONFIRMATION_SUBJECT_EN.format(clinic_name=clinic_name)
            html_body = EMAIL_CONFIRMATION_BODY_EN.format(
                clinic_name=clinic_name,
                patient_name=patient_name,
                service=service,
                datetime=datetime_str,
            )
        return NotificationService._send_email(email, subject, html_body)

    # ------------------------------------------------------------------
    # Internal transport helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _send_sms(to: str, body: str) -> bool:
        """Send an SMS via Twilio or log it if Twilio is not configured."""
        if _twilio_client and settings.TWILIO_PHONE_NUMBER:
            try:
                message = _twilio_client.messages.create(
                    body=body,
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=to,
                )
                logger.info("SMS sent — SID: %s to: %s", message.sid, to)
                return True
            except Exception as exc:
                logger.error("SMS send failed to %s: %s", to, exc)
                return False
        else:
            logger.info("[SMS NOT SENT — Twilio not configured] To: %s | Body: %s", to, body)
            return True  # return True so callers don't treat it as a hard failure

    @staticmethod
    def _send_email(to: str, subject: str, html_body: str) -> bool:
        """Send an email via SendGrid or log it if SendGrid is not configured."""
        if _sendgrid_client:
            try:
                message = Mail(
                    from_email=Email("noreply@grokdent.com", "GrokDent FL"),
                    to_emails=To(to),
                    subject=subject,
                    html_content=Content("text/html", html_body),
                )
                response = _sendgrid_client.send(message)
                logger.info(
                    "Email sent — to: %s status: %s", to, response.status_code
                )
                return True
            except Exception as exc:
                logger.error("Email send failed to %s: %s", to, exc)
                return False
        else:
            logger.info(
                "[EMAIL NOT SENT — SendGrid not configured] To: %s | Subject: %s",
                to, subject,
            )
            return True


# Module-level convenience instance
notification_service = NotificationService()
