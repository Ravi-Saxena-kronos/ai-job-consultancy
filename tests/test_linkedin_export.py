#!/usr/bin/env python3
"""LinkedIn export helpers (no network)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lib.linkedin_export import (  # noqa: E402
    dedupe_listings,
    normalize_job_url,
    JobListing,
)


def test_normalize_job_url() -> None:
    a = normalize_job_url("https://www.linkedin.com/jobs/view/1234567890/?refId=abc")
    b = normalize_job_url("https://www.linkedin.com/jobs/view/1234567890")
    assert a == b


def test_dedupe() -> None:
    jobs = [
        JobListing("Dev", "Acme", job_url="https://www.linkedin.com/jobs/view/1"),
        JobListing("Dev 2", "Acme", job_url="https://www.linkedin.com/jobs/view/1/"),
    ]
    out = dedupe_listings(jobs, set())
    assert len(out) == 1


def main() -> int:
    test_normalize_job_url()
    test_dedupe()
    print("ok: test_linkedin_export")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
