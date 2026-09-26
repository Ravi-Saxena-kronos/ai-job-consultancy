"""Send transactional email via Resend, Brevo, or SMTP (stdlib)."""

from __future__ import annotations

import json
import smtplib
import ssl
import urllib.error
import urllib.request
from email.message import EmailMessage
from typing import Callable

import re

from .config import env

_EMAIL_RE = re.compile(r"[^\s<>\"']+@[^\s<>\"']+\.[^\s<>\"']+")


def normalize_from_email(raw: str) -> str:
    """Plain email for APIs (handles 'Name <you@gmail.com>' pasted from Brevo)."""
    text = (raw or "").strip().strip('"').strip("'")
    if "<" in text and ">" in text:
        text = text.split("<", 1)[1].split(">", 1)[0].strip()
    match = _EMAIL_RE.search(text)
    email = (match.group(0) if match else text).strip().lower()
    return email


def email_provider() -> str:
    """auto | resend | brevo | smtp — auto picks first configured backend."""
    choice = env("EMAIL_PROVIDER", "auto").strip().lower()
    if choice in ("resend", "brevo", "smtp"):
        return choice
    if env("RESEND_API_KEY"):
        return "resend"
    if env("BREVO_API_KEY"):
        return "brevo"
    if env("SMTP_HOST"):
        return "smtp"
    return ""


def resolved_from_email() -> str:
    """Verified sender address for Brevo/Resend (not display name)."""
    for key in ("BREVO_SENDER_EMAIL", "EMAIL_FROM"):
        addr = normalize_from_email(env(key))
        if addr and "@" in addr:
            return addr
    return ""


def email_configured() -> bool:
    addr = resolved_from_email()
    return bool(addr and "@" in addr and email_provider())


def _from_addr() -> str:
    addr = resolved_from_email()
    if not addr or "@" not in addr:
        raise RuntimeError("EMAIL_FROM must be set to a verified sender email (e.g. your@gmail.com)")
    return addr


def _from_name() -> str:
    return env("EMAIL_FROM_NAME", "AI Job Consultancy").strip() or "AI Job Consultancy"


def _send_resend(to: str, subject: str, text: str) -> str:
    key = env("RESEND_API_KEY")
    if not key:
        raise RuntimeError("RESEND_API_KEY is not set")
    from_addr = _from_addr()
    body = json.dumps(
        {
            "from": from_addr,
            "to": [to],
            "subject": subject,
            "text": text,
        }
    ).encode()
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    raw = _http_read(req)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw or "ok"
    return str(data.get("id") or data.get("message_id") or "ok")


def _send_brevo(to: str, subject: str, text: str) -> str:
    key = env("BREVO_API_KEY")
    if not key:
        raise RuntimeError("BREVO_API_KEY is not set")
    from_addr = _from_addr()
    payload = {
        "sender": {"name": _from_name(), "email": from_addr},
        "to": [{"email": to}],
        "subject": subject,
        "textContent": text,
    }
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=body,
        headers={
            "api-key": key,
            "Content-Type": "application/json",
            "accept": "application/json",
        },
        method="POST",
    )
    raw = _http_read(req)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw or "ok"
    return str(data.get("messageId") or data.get("message_id") or "ok")


def _send_smtp(to: str, subject: str, text: str) -> str:
    host = env("SMTP_HOST").strip()
    if not host:
        raise RuntimeError("SMTP_HOST is not set")
    try:
        port = int(env("SMTP_PORT", "587"))
    except ValueError:
        port = 587
    user = env("SMTP_USER").strip() or _from_addr()
    password = env("SMTP_PASSWORD")
    if not password:
        raise RuntimeError("SMTP_PASSWORD must be set for SMTP delivery")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{_from_name()} <{_from_addr()}>"
    msg["To"] = to
    msg.set_content(text)

    if port == 465:
        with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context()) as smtp:
            smtp.login(user, password)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.ehlo()
            if smtp.has_extn("starttls"):
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()
            smtp.login(user, password)
            smtp.send_message(msg)
    return "smtp-ok"


def _http_read(req: urllib.request.Request) -> str:
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode()
    except urllib.error.HTTPError as err:
        detail = err.read().decode()
        msg = f"Email API HTTP {err.code}: {detail}"
        if "valid sender email" in detail.lower():
            msg += f" (sender used: {resolved_from_email()!r})"
        raise RuntimeError(msg) from err


_SENDERS: dict[str, Callable[[str, str, str], str]] = {
    "resend": _send_resend,
    "brevo": _send_brevo,
    "smtp": _send_smtp,
}


def send_email(to: str, subject: str, text: str) -> str:
    """Send email. Returns provider message id (or sentinel string)."""
    provider = email_provider()
    if not provider:
        raise RuntimeError(
            "No email provider configured. Set RESEND_API_KEY, BREVO_API_KEY, "
            "or SMTP_HOST + SMTP_PASSWORD (and EMAIL_FROM)."
        )
    fn = _SENDERS.get(provider)
    if not fn:
        raise RuntimeError(f"Unknown EMAIL_PROVIDER: {provider}")
    return fn(to.strip(), subject, text)
