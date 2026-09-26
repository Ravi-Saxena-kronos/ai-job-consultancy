"""Load configuration from environment (Vercel + local .env file)."""

import json
import os
from pathlib import Path


def _load_dotenv() -> None:
    # On Vercel, only use dashboard env vars (never a bundled .env file).
    if os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"):
        return
    path = Path(__file__).resolve().parents[1] / ".env"
    if not path.is_file():
        return
    parsed: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if not key:
            continue
        parsed[key] = val.strip().strip('"').strip("'")
    for key, val in parsed.items():
        if key not in os.environ:
            os.environ[key] = val


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


def _parse_service_account_json(raw: str) -> dict:
    """Parse service account JSON from Vercel env (often one line, sometimes with trailing junk)."""
    text = raw.strip()
    if not text:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON is empty")
    # Double-encoded JSON string in env
    if text.startswith('"') and text.endswith('"'):
        try:
            unquoted = json.loads(text)
            if isinstance(unquoted, str):
                text = unquoted.strip()
        except json.JSONDecodeError:
            pass
    try:
        data = json.loads(text)
    except json.JSONDecodeError as err:
        if "Extra data" in err.msg:
            data, _end = json.JSONDecoder().raw_decode(text)
        else:
            start, end = text.find("{"), text.rfind("}")
            if start < 0 or end <= start:
                raise RuntimeError(
                    "GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON. "
                    "Paste the full key file as one line in Vercel (no extra text after the closing brace)."
                ) from err
            data = json.loads(text[start : end + 1])
    if not isinstance(data, dict):
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON must be a JSON object")
    if not data.get("client_email"):
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON missing client_email")
    return data


def google_service_account_info() -> dict:
    raw = env("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON is not set")
    return _parse_service_account_json(raw)
