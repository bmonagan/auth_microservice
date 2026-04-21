import logging
import smtplib
from email.message import EmailMessage

from src.config import settings

logger = logging.getLogger(__name__)


def build_verification_link(token: str) -> str:
    base_url = settings.APP_BASE_URL.rstrip("/")
    return f"{base_url}/auth/verify-email?token={token}"


def send_verification_email(to_email: str, token: str) -> None:
    verification_link = build_verification_link(token)

    # If SMTP is not configured, log the link so dev environments can still verify users.
    if not settings.SMTP_HOST:
        logger.warning("SMTP not configured. Verification link for %s: %s", to_email, verification_link)
        return

    msg = EmailMessage()
    msg["Subject"] = "Verify your email"
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to_email
    msg.set_content(
        "Welcome! Verify your account by clicking the link below:\n\n"
        f"{verification_link}\n\n"
        "If you did not create this account, you can ignore this email."
    )

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_USE_TLS:
            server.starttls()
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)


def build_reset_link(token: str) -> str:
    base_url = settings.APP_BASE_URL.rstrip("/")
    return f"{base_url}/auth/reset-password?token={token}"


def send_password_reset_email(to_email: str, token: str) -> None:
    reset_link = build_reset_link(token)

    # If SMTP is not configured, log the link so dev environments can reset passwords.
    if not settings.SMTP_HOST:
        logger.warning("SMTP not configured. Password reset link for %s: %s", to_email, reset_link)
        return

    msg = EmailMessage()
    msg["Subject"] = "Reset your password"
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to_email
    msg.set_content(
        "You requested to reset your password. Click the link below to proceed:\n\n"
        f"{reset_link}\n\n"
        f"This link will expire in {settings.PASSWORD_RESET_EXPIRE_MINUTES} minutes.\n\n"
        "If you did not request this, you can ignore this email."
    )

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_USE_TLS:
            server.starttls()
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)
