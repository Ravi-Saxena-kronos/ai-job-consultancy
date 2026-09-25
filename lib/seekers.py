"""Seeker row helpers — latest row wins when sheet has history appends."""

from __future__ import annotations

from typing import Optional

from . import sheet_schema, sheets


def _is_header_row(row: list) -> bool:
    if not row:
        return False
    c0 = str(row[0]).strip().lower().replace(" ", "_")
    if c0 in ("seeker_id", "seekerid"):
        return True
    if len(row) > 1 and str(row[1]).strip().lower() == "email":
        return True
    return False


def _row_to_seeker(row: list[str]) -> dict[str, str]:
    """Map SEEKERS row by column position (A=seeker_id, B=email, …)."""
    keys = sheet_schema.SEEKERS_HEADERS
    padded = list(row) + [""] * max(0, len(keys) - len(row))
    return {keys[i]: str(padded[i]) for i in range(len(keys))}


def all_seeker_rows() -> list[dict[str, str]]:
    raw = sheets.read_all("SEEKERS")
    if not raw:
        return []
    out: list[dict[str, str]] = []
    for i, row in enumerate(raw):
        if i == 0 and _is_header_row(row):
            continue
        if not any(str(c).strip() for c in row):
            continue
        out.append(_row_to_seeker(row))
    return out


def normalize_utr(utr: str) -> str:
    return "".join(ch for ch in (utr or "").strip() if not ch.isspace())


def latest_by_utr(utr: str) -> Optional[dict[str, str]]:
    want = normalize_utr(utr)
    if not want:
        return None
    matches = [
        r
        for r in all_seeker_rows()
        if normalize_utr(r.get("utr") or "") == want
    ]
    return matches[-1] if matches else None


def latest_by_id(seeker_id: str) -> Optional[dict[str, str]]:
    seeker_id = seeker_id.strip()
    matches = [r for r in all_seeker_rows() if (r.get("seeker_id") or "").strip() == seeker_id]
    return matches[-1] if matches else None


def latest_by_email(email: str) -> Optional[dict[str, str]]:
    email = email.strip().lower()
    matches = [r for r in all_seeker_rows() if (r.get("email") or "").strip().lower() == email]
    return matches[-1] if matches else None


def active_seekers() -> list[dict[str, str]]:
    """One dict per seeker_id — latest row only."""
    by_id: dict[str, dict[str, str]] = {}
    for row in all_seeker_rows():
        sid = (row.get("seeker_id") or "").strip()
        if sid:
            by_id[sid] = row
    out = []
    for row in by_id.values():
        if (row.get("payment_status") or "").lower() != "verified":
            continue
        status = (row.get("status") or "").lower()
        if status not in {"active", "pending_resume"}:
            continue
        try:
            if int(row.get("posts_remaining") or "0") <= 0 and status == "active":
                continue
        except ValueError:
            pass
        if status == "pending_resume":
            continue
        out.append(row)
    return out
