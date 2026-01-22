import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import SecretStr, EmailStr

from api.src.config import settings

logger = logging.getLogger(__name__)


# Configure email connection
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=SecretStr(settings.MAIL_PASSWORD),
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
)

fm = FastMail(conf)



# Jinja2 template environment
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "templates" / "email"

jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)

def render_template(template_name: str, context: dict) -> str:
    template = jinja_env.get_template(template_name)
    return template.render(**context)



class EmailService:
    @staticmethod
    async def send_password_reset_email(
        email: EmailStr,
        reset_token: str,
        user_name: str | None = None,
    ) -> bool:
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

        context = {
            "user_name": user_name,
            "reset_link": reset_link,
            "expiry_minutes": settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
        }

        html_body = render_template("password_reset.html", context)

        message = MessageSchema(
            subject="Reset Your MediReminder Password",
            recipients=[email], #type: ignore
            body=html_body,
            subtype=MessageType.html,
        )

        try:
            await fm.send_message(message)
            logger.info("Password reset email sent to %s", email)
            return True
        except Exception as exc:
            logger.error("Failed to send reset email to %s: %s", email, exc)
            return False

    @staticmethod
    async def send_password_changed_notification(
        email: str,
        user_name: str | None = None,
    ) -> bool:
        context = {"user_name": user_name}

        html_body = render_template("password_changed.html", context)

        message = MessageSchema(
            subject="Your MediReminder Password Has Been Changed",
            recipients=[email], #type: ignore
            body=html_body,
            subtype=MessageType.html,
        )

        try:
            await fm.send_message(message)
            logger.info("Password change notification sent to %s", email)
            return True
        except Exception as exc:
            logger.error("Failed to send notification to %s: %s", email, exc)
            return False
