"""Tailor resume text per job post (OpenAI or keyword fallback)."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from .config import env

_SKILL_WORDS = re.compile(
    r"\b(?:python|java|devops|aws|azure|kubernetes|docker|terraform|jenkins|"
    r"react|angular|node\.?js|sql|excel|tally|sap|sales|marketing|hr|recruitment|"
    r"accounting|gst|nursing|teaching|bpo|customer service|communication)\b",
    re.I,
)


def _openai_tailor(
    base: str,
    job_title: str,
    job_post: str,
    seeker_role: str,
) -> str:
    key = env("OPENAI_API_KEY").strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY not set")
    model = env("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    system = (
        "You edit resumes for job applications. Output plain text only. "
        "Never invent employers, degrees, dates, or job titles the candidate did not have. "
        "You may add a section 'Skills aligned with this role' with keywords from the job post "
        "that are plausible given the resume. Keep existing sections."
    )
    user = (
        f"Target role: {seeker_role or job_title}\n"
        f"Job title: {job_title}\n"
        f"Job post:\n{job_post[:12000]}\n\n"
        f"Candidate resume:\n{base[:12000]}\n\n"
        "Return the full updated resume text."
    )
    body = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.3,
        }
    ).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode())
    choice = data["choices"][0]["message"]["content"]
    return (choice or "").strip()


def _fallback_tailor(base: str, job_title: str, job_post: str) -> str:
    blob = f"{job_title}\n{job_post}"
    found = sorted({m.group(0) for m in _SKILL_WORDS.finditer(blob)})
    missing = [s for s in found if s.lower() not in base.lower()]
    if not missing:
        return base
    extra = "\n\nSkills aligned with this role\n" + "\n".join(f"- {s}" for s in missing[:25])
    return base.rstrip() + extra


def tailor_resume(
    base_resume: str,
    job_title: str,
    job_post_text: str,
    seeker_role: str = "",
) -> str:
    base = (base_resume or "").strip()
    if not base:
        raise ValueError("empty base resume")
    job_post = (job_post_text or "").strip()
    if not job_post:
        job_post = job_title
    try:
        if env("OPENAI_API_KEY").strip():
            return _openai_tailor(base, job_title, job_post, seeker_role)
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, RuntimeError):
        pass
    return _fallback_tailor(base, job_title, job_post)
