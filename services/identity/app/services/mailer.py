import smtplib
from email.message import EmailMessage

from .. import settings


PROVIDER_DEFAULTS = {
    "gmail": {"host": "smtp.gmail.com", "port": 587, "use_tls": True, "use_ssl": False},
    "outlook": {"host": "smtp.office365.com", "port": 587, "use_tls": True, "use_ssl": False},
    "hotmail": {"host": "smtp.office365.com", "port": 587, "use_tls": True, "use_ssl": False},
    "live": {"host": "smtp.office365.com", "port": 587, "use_tls": True, "use_ssl": False},
}


class MailConfigurationError(RuntimeError):
    pass


class MailDeliveryError(RuntimeError):
    pass


def _provider_settings() -> dict:
    return PROVIDER_DEFAULTS.get(settings.SMTP_PROVIDER, {})


def smtp_is_configured() -> bool:
    provider_defaults = _provider_settings()
    host = settings.SMTP_HOST or provider_defaults.get("host", "")
    port = settings.SMTP_PORT or provider_defaults.get("port", 0)
    return bool(host and port and settings.SMTP_USERNAME and settings.SMTP_PASSWORD and settings.SMTP_FROM_EMAIL)


def _smtp_config() -> dict:
    provider_defaults = _provider_settings()
    host = settings.SMTP_HOST or provider_defaults.get("host", "")
    port = settings.SMTP_PORT or provider_defaults.get("port", 0)
    use_tls = settings.SMTP_USE_TLS if settings.SMTP_HOST else provider_defaults.get("use_tls", settings.SMTP_USE_TLS)
    use_ssl = settings.SMTP_USE_SSL if settings.SMTP_HOST else provider_defaults.get("use_ssl", settings.SMTP_USE_SSL)

    if not host or not port:
        raise MailConfigurationError("SMTP host/port not configured")
    if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        raise MailConfigurationError("SMTP credentials not configured")
    if not settings.SMTP_FROM_EMAIL:
        raise MailConfigurationError("SMTP sender email not configured")

    return {
        "host": host,
        "port": port,
        "use_tls": use_tls,
        "use_ssl": use_ssl,
    }


def send_password_reset_email(recipient_email: str, reset_url: str) -> None:
    config = _smtp_config()

    message = EmailMessage()
    message["Subject"] = "Reset your ProShare password"
    message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    message["To"] = recipient_email
    message.set_content(
        "We received a request to reset your ProShare password.\n\n"
        f"Open this link to choose a new password:\n{reset_url}\n\n"
        f"This link expires in {settings.PASSWORD_RESET_TOKEN_TTL_MINUTES} minutes.\n"
        "If you did not request a reset, you can safely ignore this email.\n"
    )

    smtp_cls = smtplib.SMTP_SSL if config["use_ssl"] else smtplib.SMTP
    try:
        with smtp_cls(config["host"], config["port"], timeout=20) as smtp:
            smtp.ehlo()
            if config["use_tls"] and not config["use_ssl"]:
                smtp.starttls()
                smtp.ehlo()
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp.send_message(message)
    except (smtplib.SMTPException, OSError) as exc:
        raise MailDeliveryError(f"Unable to deliver password reset email: {exc}") from exc
