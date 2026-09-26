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


def existing_job_urls(tab_title: Optional[str] = None) -> set[str]:
    from . import sheets

    title = tab_title or sheets.applications_tab_name()
    rows = sheets.read_tab(title)
    if not rows:
        return set()
    headers = [str(h).strip().lower().replace(" ", "_") for h in rows[0]]
    try:
        idx = headers.index("job_url")
    except ValueError:
        return set()
    out: set[str] = set()
    for row in rows[1:]:
        if idx < len(row):
            norm = normalize_job_url(str(row[idx]))
            if norm:
                out.add(norm)
    return out


def dedupe_listings(jobs: list[JobListing], known_urls: set[str]) -> list[JobListing]:
    seen: set[str] = set(known_urls)
    out: list[JobListing] = []
    for job in jobs:
        key = normalize_job_url(job.job_url)
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
    hr = hr_verify.extract_from_description(job.description)
    if hr and hr_verify.verified_enough(hr, "jd_parse"):
        return hr, "Y", "jd_parse"
    return hr or "", "N", "linkedin_export"


def application_row(
    job: JobListing,
    *,
    seeker_id: str = "",
    companies: Optional[list[dict]] = None,
) -> list[str]:
    hr_email, verified, method = enrich_hr_email(job, companies)
    status = "linkedin_lead" if verified == "Y" and hr_email else "skipped_no_email"
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
