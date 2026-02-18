import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import EmailStr, SecretStr

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

from api.src.config_package import settings

# EMAIL CONNECTION SETUP
# ==============================================================================
# Initialize FastMail connection configuration with settings from environment.
# Credentials are loaded from .env file via settings (Pydantic BaseSettings).
# Note: Template rendering is handled by Jinja2 environment (see TEMPLATES_DIR below)
conf = ConnectionConfig(
    # SMTP server username (email address or username).
    MAIL_USERNAME=settings.MAIL_USERNAME,
    # SMTP server password (stored securely as SecretStr to prevent logging).
    MAIL_PASSWORD=settings.MAIL_PASSWORD.get_secret_value(),
    # Sender email address (From: header in outgoing emails).
    MAIL_FROM=settings.MAIL_FROM,
    # SMTP server port (typically 587 for STARTTLS, 465 for SSL).
    MAIL_PORT=settings.MAIL_PORT,
    # SMTP server hostname (e.g., smtp.gmail.com).
    MAIL_SERVER=settings.MAIL_SERVER,
    # Display name for sender (appears as "MAIL_FROM_NAME <MAIL_FROM>" in email clients).
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    # Enable STARTTLS encryption for the connection (upgrade connection after initial connection).
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    # Enable SSL/TLS encryption from the start of connection (port 465 typically).
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    # Use credentials for authentication (disable for unauthenticated servers).
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    # Validate SSL certificates (set False only for testing with self-signed certs).
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
)

# Create FastMail instance with the above configuration.
# This instance will be used to send all emails asynchronously.
fm = FastMail(conf)
# Initialize logger for this module to track email operations and errors.
logger = logging.getLogger(__name__)


# JINJA2 TEMPLATE ENVIRONMENT
# Get absolute path to email templates directory.
# Traverse up from this file: service.py -> email -> services -> src -> api.
CURRENT_DIR = Path(__file__).resolve().parent
# Construct full path to email templates folder.
TEMPLATES_DIR = CURRENT_DIR / "templates" / "email"

# Initialize Jinja2 environment for rendering email templates.
# FileSystemLoader: Load templates from TEMPLATES_DIR.
# select_autoescape: Auto-escape HTML/XML content to prevent XSS vulnerabilities.
jinja_env = Environment(
    # Specify the directory to load templates from.
    loader=FileSystemLoader(TEMPLATES_DIR),
    # Auto-escape unsafe characters in HTML/XML templates (for security).
    autoescape=select_autoescape(["html", "xml"]),
)

def render_template(template_name: str, context: dict) -> str:
    """
    Render a Jinja2 template with the provided context data.

    Args:
        template_name: Name of the template file (e.g., "password_reset.html")
        context: Dictionary of variables to inject into the template

    Returns:
        Rendered HTML string ready to send in email body
    """
    # Load template by name from Jinja2 environment.
    template = jinja_env.get_template(template_name)
    # Render template with context variables (replacing {{ variable }} placeholders).
    return template.render(**context)



class EmailService:
    """
    Email service for sending transactional emails to users.
    Handles password resets, notifications, and account events.
    All methods are static and async for non-blocking I/O.
    """

    @staticmethod
    async def send_password_reset_email(
        email: EmailStr,
        reset_token: str,
        user_name: str | None = None,
    ) -> bool:
        """
        Send password reset email with reset link.

        Args:
            email: Recipient email address (validated by Pydantic)
            reset_token: Secure token for password reset (from auth service)
            user_name: Optional user's display name for personalization

        Returns:
            True if email sent successfully, False if sending failed

        Troubleshooting:
            - SMTP connection errors: Verify MAIL_SERVER, MAIL_PORT, credentials
            - SSL/TLS issues: Check MAIL_STARTTLS and MAIL_SSL_TLS settings
            - Template not found: Verify password_reset.html exists in templates folder
        """
        # Construct reset link with token for frontend redirect.
        # Token should be validated server-side when user submits new password.
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

        # Build dictionary of variables to inject into email template.
        # These map to {{ placeholder }} syntax in password_reset.html.
        context = {
            # User's display name (optional, for personalization).
            "user_name": user_name,
            # Reset link that user will click in email client.
            "reset_link": reset_link,
            # Token expiry time (show user how long link is valid for).
            "expiry_minutes": settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
        }

        # Render HTML email body by injecting context into template.
        # Returns complete HTML string with all variables replaced.
        html_body = render_template("password_reset.html", context)

        # Create FastMail MessageSchema (defines email structure and content).
        message = MessageSchema(
            # Email subject line shown in user's inbox.
            subject="Reset Your MediReminder Password",
            # List of recipient email addresses.
            recipients=[email],  #type: ignore
            # HTML body content (rendered from template above).
            body=html_body,
            # Set message type to HTML (not plain text).
            subtype=MessageType.html,
        )

        try:
            # Send email asynchronously via FastMail connection.
            # Awaits connection to SMTP server and delivery confirmation.
            await fm.send_message(message)
            # Log successful email delivery for audit trail.
            logger.info("Password reset email sent to %s", email)
            # Return successa status.
            return True
        except Exception as exc:
            # Log error details including email address and exception message.
            logger.error("Failed to send reset email to %s: %s", email, exc)
            # Log SMTP configuration for debugging connection issues.
            logger.error("Email config - Server: %s, Port: %s, Username: %s, STARTTLS: %s, SSL_TLS: %s",
                        settings.MAIL_SERVER, settings.MAIL_PORT, settings.MAIL_USERNAME,
                        settings.MAIL_STARTTLS, settings.MAIL_SSL_TLS)
            # Return failure status.
            return False

    @staticmethod
    async def send_password_changed_notification(
        email: str,
        user_name: str | None = None,
    ) -> bool:
        """
        Send notification email confirming password change.

        Args:
            email: Recipient email address
            user_name: Optional user's display name for personalization

        Returns:
            True if email sent successfully, False if sending failed

        Notes:
            - This is a security notification, send promptly after password change
            - User should verify they initiated the change
        """
        # Build context dictionary for template rendering.
        context = {
            # User's display name (optional, for personalization).
            "user_name": user_name
        }

        # Render HTML email body with context variables injected.
        html_body = render_template("password_changed.html", context)

        # Create message schema for password change notification.
        message = MessageSchema(
            # Clear subject indicating account security event.
            subject="Your MediReminder Password Has Been Changed",
            # Recipient email address.
            recipients=[email],  #type: ignore
            # HTML body with rendered template.
            body=html_body,
            # Set message type to HTML (not plain text).
            subtype=MessageType.html,
        )

        try:
            # Send email asynchronously via FastMail connection.
            # Awaits connection to SMTP server and delivery confirmation.
            await fm.send_message(message)
            # Log successful email delivery for audit trail.
            logger.info("Password change notification sent to %s", email)
            # Return success status.
            return True
        except Exception as exc:
            # Log error details including email address and exception message.
            logger.error("Failed to send notification to %s: %s", email, exc)
            # Return failure status.
            return False

    @staticmethod
    async def send_account_linked_notification(
        email: str,
        user_name: str | None = None,
    ) -> bool:
        """
        Send security notification when a Google account is linked.

        Args:
            email: Recipient email address
            user_name: Optional user's display name for personalization

        Returns:
            True if email sent successfully, False if sending failed

        Notes:
            - This is a security alert, send promptly when account linking occurs
            - User should verify they initiated the Google account linking
        """
        # Build context dictionary for template rendering.
        # Maps to {{ placeholder }} syntax in account_linked.html template.
        context = {
            # User's display name (optional, for personalization).
            "user_name": user_name,
            # Service being linked (Google in this case).
            "linked_service": "Google"
        }

        # Render HTML email body by injecting context into template.
        # Returns complete HTML string with all variables replaced.
        html_body = render_template("account_linked.html", context)

        # Create FastMail MessageSchema for account linking security alert.
        message = MessageSchema(
            # Subject line indicating security-related action.
            subject="Security Alert: Google Account Linked",
            # Recipient email address (list required by FastMail).
            recipients=[email],  #type: ignore
            # HTML body with rendered template.
            body=html_body,
            # Set message type to HTML (not plain text).
            subtype=MessageType.html,
        )

        try:
            # Send email asynchronously via FastMail connection.
            # Awaits connection to SMTP server and delivery confirmation.
            await fm.send_message(message)
            # Log successful email delivery for audit trail.
            logger.info("Account linked email sent to %s", email)
            # Return success status.
            return True
        except Exception as exc:
            # Log error details including email address and exception message.
            logger.error("Failed to send account linked email to %s: %s", email, exc)
            # Log SMTP configuration for debugging connection issues.
            logger.error("Email config - Server: %s, Port: %s, Username: %s, STARTTLS: %s, SSL_TLS: %s",
                        settings.MAIL_SERVER, settings.MAIL_PORT, settings.MAIL_USERNAME,
                        settings.MAIL_STARTTLS, settings.MAIL_SSL_TLS)
            # Return failure status.
            return False

    @staticmethod
    async def send_welcome_email(
        email: str,
        user_name: str | None = None,
    ) -> bool:
        """
        Send welcome email to new users.

        Args:
            email: Recipient email address
            user_name: Optional user's display name for personalization

        Returns:
            True if email sent successfully, False if sending failed

        Notes:
            - Send this email immediately after user account creation
            - First touchpoint for user onboarding experience
        """
        # Build context dictionary for template rendering.
        # Maps to {{ placeholder }} syntax in welcome.html template.
        context = {
            # User's display name (optional, for personalization).
            "user_name": user_name
        }

        # Render HTML email body by injecting context into template.
        # Returns complete HTML string with all variables replaced.
        html_body = render_template("welcome.html", context)

        # Create FastMail MessageSchema for welcome email to new user.
        message = MessageSchema(
            # Friendly subject line for account welcome notification.
            subject="Welcome to MediReminder - Your Health Companion",
            # Recipient email address (list required by FastMail).
            recipients=[email],  #type: ignore
            # HTML body with rendered template (includes onboarding info).
            body=html_body,
            # Set message type to HTML (not plain text).
            subtype=MessageType.html,
        )

        try:
            # Send email asynchronously via FastMail connection.
            # Awaits connection to SMTP server and delivery confirmation.
            await fm.send_message(message)
            # Log successful email delivery for audit trail.
            logger.info("Welcome email sent to %s", email)
            # Return success status.
            return True
        except Exception as exc:
            # Log error details including email address and exception message.
            logger.error("Failed to send welcome email to %s: %s", email, exc)
            # Log SMTP configuration for debugging connection issues.
            logger.error("Email config - Server: %s, Port: %s, Username: %s, STARTTLS: %s, SSL_TLS: %s",
                        settings.MAIL_SERVER, settings.MAIL_PORT, settings.MAIL_USERNAME,
                        settings.MAIL_STARTTLS, settings.MAIL_SSL_TLS)
            # Return failure status.
            return False
