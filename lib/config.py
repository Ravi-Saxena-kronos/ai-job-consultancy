"""Load configuration from environment (Vercel + local .env file)."""

import json
import os
from pathlib import Path


def _load_dotenv() -> None:
    path = Path(__file__).resolve().parents[1] / ".env"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = val.strip().strip('"').strip("'")


_load_dotenv()


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def registration_fee_inr() -> int:
    try:
        return int(env("REGISTRATION_FEE_INR", "99"))
    except ValueError:
        return 99


def upi_vpa() -> str:
    return env("UPI_VPA", "8595066768@amazonpay")


def upi_payee_name() -> str:
    return env("UPI_PAYEE_NAME", "AI Job Consultancy")


def default_posts_remaining() -> int:
    try:
        return int(env("DEFAULT_POSTS_REMAINING", "5"))
    except ValueError:
        return 5


def google_service_account_info() -> dict:
    raw = env("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON is not set")
    return json.loads(raw)
