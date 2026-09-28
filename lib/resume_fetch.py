"""Fetch and extract plain text from resume URLs (Drive, PDF, text)."""

from __future__ import annotations

import io
import re
import urllib.parse
import urllib.request

_MAX_BYTES = 2_500_000


def _drive_export_url(url: str) -> str:
    url = url.strip()
    m = re.search(r"/file/d/([a-zA-Z0-9_-]+)", url)
    if m:
        fid = m.group(1)
        return f"https://drive.google.com/uc?export=download&id={fid}"
    m = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", url)
    if m:
        return f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    return url


def _fetch_bytes(url: str) -> bytes:
    url = _drive_export_url(url)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "AI-Job-Consultancy/1.0"},
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        data = resp.read(_MAX_BYTES + 1)
    if len(data) > _MAX_BYTES:
        raise ValueError("resume file too large")
    return data


def _pdf_to_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    parts: list[str] = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts).strip()


def fetch_resume_text(resume_url: str) -> tuple[str, str]:
    """Returns (text, error_message). error empty on success."""
    url = (resume_url or "").strip()
    if not url or url.startswith("(") or len(url) < 8:
        return "", "resume_url missing or not a link"
    if "drive.google" in url or "docs.google" in url:
        try:
            data = _fetch_bytes(url)
        except Exception as err:
            return "", f"could not download Drive file: {err}"
        if data[:4] == b"%PDF":
            try:
                return _pdf_to_text(data), ""
            except Exception as err:
                return "", f"PDF parse failed: {err}"
        try:
            return data.decode("utf-8", errors="replace").strip(), ""
        except Exception:
            return "", "Drive file is not text or PDF"
    if url.lower().endswith(".pdf") or ".pdf?" in url.lower():
        try:
            data = _fetch_bytes(url)
            return _pdf_to_text(data), ""
        except Exception as err:
            return "", f"PDF fetch/parse failed: {err}"
    try:
        data = _fetch_bytes(url)
        if data[:4] == b"%PDF":
            return _pdf_to_text(data), ""
        return data.decode("utf-8", errors="replace").strip(), ""
    except Exception as err:
        return "", f"fetch failed: {err}"
