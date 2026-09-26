"""LinkedIn job listing model, dedupe, and JOB_APPLICATIONS row building."""

from __future__ import annotations

import datetime as dt
import re
import uuid
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import parse_qs, urlparse, urlunparse

from . import hr_verify


@dataclass
class JobListing:
    title: str
    company: str
    location: str = ""
    job_url: str = ""
    linkedin_job_id: str = ""
    listed_at: str = ""
    description: str = ""


def normalize_company(name: str) -> str:
    s = (name or "").strip().lower()
    for junk in (
        "private limited",
        "pvt. ltd.",
        "pvt ltd",
        "llc",
        "inc.",
        "inc",
        "ltd.",
        "ltd",
    ):
        s = s.replace(junk, "")
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def normalize_job_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    parsed = urlparse(url if "://" in url else f"https://{url}")
    path = parsed.path.rstrip("/")
    if "/jobs/view/" in path:
        job_id = path.split("/jobs/view/")[-1].split("/")[0]
        if job_id.isdigit():
            path = f"/jobs/view/{job_id}"
    qs = parse_qs(parsed.query)
    keep = {k: qs[k] for k in ("currentJobId",) if k in qs}
    query = "&".join(f"{k}={v[0]}" for k, v in keep.items())
    return urlunparse((parsed.scheme or "https", parsed.netloc.lower(), path, "", query, ""))


def listing_dedupe_key(job: JobListing) -> str:
    """Unique key per lead — content posts must not all share the search URL."""
    url = normalize_job_url(job.job_url or "")
    if url and "/content-export/" in url:
        return url
    emails = hr_verify.extract_post_emails(job.description or "", allow_free_mail=True)
    if emails:
        return f"mailto:{hr_verify.normalize_email(emails[0])}"
    if url and "/search/results/content" not in url:
        return url
    company = normalize_company(job.company)
    title = (job.title or "").strip().lower()
    if company or title:
        return f"post:{company}|{title}"
    return url or ""


def existing_dedupe_keys(tab_title: Optional[str] = None) -> set[str]:
    from . import sheets

    title = tab_title or sheets.applications_tab_name()
    rows = sheets.read_tab(title)
    if not rows:
        return set()
    headers = [str(h).strip().lower().replace(" ", "_") for h in rows[0]]
    out: set[str] = set()
    for row in rows[1:]:
        padded = row + [""] * (len(headers) - len(row))
        data = {headers[i]: padded[i] for i in range(len(headers))}
        norm = normalize_job_url(str(data.get("job_url") or ""))
        if norm:
            out.add(norm)
        hr = hr_verify.normalize_email(str(data.get("hr_email") or ""))
        if hr and "@" in hr:
            out.add(f"mailto:{hr}")
    return out


def existing_job_urls(tab_title: Optional[str] = None) -> set[str]:
    return existing_dedupe_keys(tab_title)


def dedupe_listings(jobs: list[JobListing], known_keys: set[str]) -> list[JobListing]:
    seen: set[str] = set(known_keys)
    out: list[JobListing] = []
    for job in jobs:
        key = listing_dedupe_key(job)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(job)
    return out


def enrich_hr_email(job: JobListing, companies: Optional[list[dict]] = None) -> tuple[str, str, str]:
    """Returns hr_email, email_verified (Y/N), verification_method."""
    from . import sheets

    companies = companies if companies is not None else sheets.rows_as_dicts("COMPANIES")
    hr = sheets.find_verified_company_email(job.company, companies)
    if hr and hr_verify.verified_enough(hr, "company_csv"):
        return hr, "Y", "company_csv"
    text = job.description or ""
    hr, method = hr_verify.pick_best_email(text)
    if not hr:
        posts = hr_verify.extract_post_emails(text, allow_free_mail=True)
        hr = posts[0] if posts else ""
        if not hr:
            work = hr_verify.extract_work_emails(text)
            hr = work[0] if work else ""
        method = "linkedin_export"
    elif method == "linkedin_export" and hr and hr_verify.verified_enough(hr, "content_parse"):
        method = "content_parse"
    verified = "Y" if hr and hr_verify.verified_enough(hr, method) else "N"
    return hr or "", verified, method


def application_row(
    job: JobListing,
    *,
    seeker_id: str = "",
    companies: Optional[list[dict]] = None,
) -> list[str]:
    hr_email, verified, method = enrich_hr_email(job, companies)
    status = "pending_send" if hr_email else "skipped_no_email"
    app_id = "LNK-" + uuid.uuid4().hex[:8].upper()
    today = dt.date.today().isoformat()
    return [
        app_id,
        seeker_id or "LINKEDIN_EXPORT",
        job.title,
        job.company,
        job.location,
        normalize_job_url(job.job_url) or job.job_url,
        hr_email,
        verified,
        method,
        status,
        today,
        "",
    ]


APPLICATION_HEADERS = [
    "application_id",
    "seeker_id",
    "title",
    "company",
    "location",
    "job_url",
    "hr_email",
    "email_verified",
    "verification_method",
    "status",
    "applied_at",
    "hr_message_id",
]
