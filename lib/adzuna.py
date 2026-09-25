"""Adzuna India job search (listings only — no apply API)."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

from .config import env

BASE = "https://api.adzuna.com/v1/api/jobs/in/search/1"


def search_jobs(what: str, where: str = "India", max_days_old: int = 7, limit: int = 20) -> list[dict[str, Any]]:
    app_id = env("ADZUNA_APP_ID")
    app_key = env("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        return []

    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": str(min(limit, 50)),
        "what": what,
        "where": where,
        "max_days_old": str(max_days_old),
        "sort_by": "date",
    }
    url = BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "ai-job-consultancy/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())

    out = []
    for row in data.get("results") or []:
        company = (row.get("company") or {}).get("display_name") or ""
        location = (row.get("location") or {}).get("display_name") or ""
        out.append(
            {
                "title": row.get("title") or "",
                "company": company,
                "location": location,
                "job_url": row.get("redirect_url") or "",
                "description": row.get("description") or "",
                "created": row.get("created") or "",
                "adzuna_id": str(row.get("id") or ""),
            }
        )
    return out
