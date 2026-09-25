"""Razorpay orders + webhook signature (stdlib only)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import urllib.error
import urllib.request

from .config import env, registration_fee_inr


def enabled() -> bool:
    return bool(env("RAZORPAY_KEY_ID") and env("RAZORPAY_KEY_SECRET"))


def key_id() -> str:
    return env("RAZORPAY_KEY_ID")


def create_order(seeker_id: str, receipt: str) -> dict:
    secret = env("RAZORPAY_KEY_SECRET")
    kid = env("RAZORPAY_KEY_ID")
    if not secret or not kid:
        raise RuntimeError("Razorpay is not configured")

    fee = registration_fee_inr()
    amount_paise = fee * 100
    body = json.dumps(
        {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt[:40],
            "notes": {"seeker_id": seeker_id},
        }
    ).encode()
    req = urllib.request.Request(
        "https://api.razorpay.com/v1/orders",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": _basic_auth(kid, secret),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as err:
        detail = err.read().decode()
        raise RuntimeError(f"Razorpay order failed: {err.code} {detail}") from err


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    webhook_secret = env("RAZORPAY_WEBHOOK_SECRET")
    if not webhook_secret or not signature:
        return False
    digest = hmac.new(webhook_secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature)


def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    secret = env("RAZORPAY_KEY_SECRET")
    if not secret:
        return False
    payload = f"{order_id}|{payment_id}"
    expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _basic_auth(user: str, password: str) -> str:
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return f"Basic {token}"
