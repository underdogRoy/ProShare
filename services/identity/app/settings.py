import os


def _env_flag(name: str, default: bool) -> bool:
    return os.getenv(name, str(default).lower()).lower() in {"1", "true", "yes", "on"}


SMTP_PROVIDER = os.getenv("SMTP_PROVIDER", "").strip().lower()
SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "0") or "0")
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "").strip()
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "ProShare").strip()
SMTP_USE_TLS = _env_flag("SMTP_USE_TLS", True)
SMTP_USE_SSL = _env_flag("SMTP_USE_SSL", False)

PASSWORD_RESET_TOKEN_TTL_MINUTES = int(os.getenv("PASSWORD_RESET_TOKEN_TTL_MINUTES", "30"))
PASSWORD_RESET_URL_BASE = os.getenv("PASSWORD_RESET_URL_BASE", "http://127.0.0.1:5173").strip()
IDENTITY_SHOW_RESET_LINK = _env_flag("IDENTITY_SHOW_RESET_LINK", True)
