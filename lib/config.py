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
    file_hint = env("GOOGLE_SERVICE_ACCOUNT_FILE").strip()
    if file_hint:
        path = Path(file_hint)
        if not path.is_file():
            path = Path(__file__).resolve().parents[1] / file_hint
        if path.is_file():
            return _parse_service_account_json(path.read_text(encoding="utf-8"))
        raise RuntimeError(f"GOOGLE_SERVICE_ACCOUNT_FILE not found: {file_hint}")
    raw = env("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw:
        raise RuntimeError(
            "GOOGLE_SERVICE_ACCOUNT_JSON is not set. "
            "Copy from Vercel into .env (one line) or set GOOGLE_SERVICE_ACCOUNT_FILE=path/to/key.json"
        )
    return _parse_service_account_json(raw)


def _truthy_string(raw: str) -> bool:
    return raw.strip().strip('"').strip("'").lower() in ("1", "true", "yes", "on")


def _env_truthy(name: str) -> bool:
    return _truthy_string(env(name, ""))


def _test_lab_enabled_from_environ() -> bool:
    if _env_truthy("TEST_LAB_ENABLED") or _env_truthy("ENABLE_TEST_LAB"):
        return True
    for key, val in os.environ.items():
        upper = key.upper()
        if upper in ("TEST_LAB_ENABLED", "ENABLE_TEST_LAB") and _truthy_string(val):
            return True
    return False


def test_lab_enabled() -> bool:
    return _test_lab_enabled_from_environ()


def test_lab_env_status() -> dict[str, bool | int]:
    """Safe debug for /api/public_config (no secret values)."""
    found = False
    length = 0
    for key, val in os.environ.items():
        if key.upper() == "TEST_LAB_ENABLED":
            found = True
            length = len(val.strip())
            break
    return {
        "env_key_present": found,
        "env_value_length": length,
        "enabled": test_lab_enabled(),
    }


def test_lab_secret() -> str:
    return env("TEST_LAB_SECRET", "").strip() or env("ADMIN_SECRET", "").strip()


def test_lab_max_applies() -> int:
    try:
        return max(1, min(15, int(env("TEST_LAB_MAX_APPLIES", "3"))))
    except ValueError:
        return 3


def test_hr_redirect() -> str:
    """If set, test-lab HR mail goes here instead of real company HR (safe dry run)."""
    return env("TEST_HR_REDIRECT", "").strip()
