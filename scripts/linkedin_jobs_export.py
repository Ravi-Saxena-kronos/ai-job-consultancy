#!/usr/bin/env python3
"""LinkedIn Jobs search (manual login) → Google Sheet JOB_APPLICATIONS."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lib import linkedin_export, linkedin_scrape, seekers, sheets  # noqa: E402
from lib.linkedin_export import APPLICATION_HEADERS  # noqa: E402


def _write_xlsx(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    try:
        from openpyxl import Workbook
    except ImportError:
        raise RuntimeError("Install openpyxl or use --csv instead")
    wb = Workbook()
    ws = wb.active
    ws.title = "jobs"
    ws.append(headers)
    for row in rows:
        ws.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def _write_csv(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export LinkedIn jobs to Google Sheet")
    parser.add_argument("--role", help="Job keywords (default: seeker target_role)")
    parser.add_argument("--location", help="Location (default: seeker location)")
    parser.add_argument("--seeker-id", help="Tie rows to APS-XXXX and default role/location")
    parser.add_argument("--max-jobs", type=int, default=25)
    parser.add_argument("--fetch-descriptions", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--import-companies", action="store_true", help="Append verified HR emails to COMPANY_VERIFIED")
    parser.add_argument("--output", help="Optional backup .xlsx or .csv path")
    parser.add_argument(
        "--profile-dir",
        default=str(ROOT / "data" / "linkedin-browser-profile"),
        help="Persistent Chromium profile (login saved here)",
    )
    args = parser.parse_args()

    role = (args.role or "").strip()
    location = (args.location or "").strip()
    seeker_id = (args.seeker_id or "").strip()
    if seeker_id:
        row = seekers.latest_by_id(seeker_id)
        if not row:
            print(f"Seeker not found: {seeker_id}", file=sys.stderr)
            return 2
        if not role:
            role = (row.get("target_role") or row.get("domain") or "").strip()
        if not location:
            location = (row.get("location") or "").strip()
    if not role:
        print("Provide --role or --seeker-id with target_role in sheet", file=sys.stderr)
        return 2
    location = location or "India"

    tab = sheets.applications_tab_name()
    print(f"Sheet tab: {tab}")
    known = linkedin_export.existing_job_urls(tab)
    companies = sheets.rows_as_dicts("COMPANIES")

    jobs = linkedin_scrape.scrape_linkedin_jobs(
        role,
        location,
        max_jobs=args.max_jobs,
        user_data_dir=args.profile_dir,
        headless=False,
        fetch_descriptions=args.fetch_descriptions,
    )
    if not jobs:
        print(
            "No jobs scraped. Log in in the browser window, or LinkedIn changed the page — see docs/LINKEDIN-EXPORT.md",
            file=sys.stderr,
        )
        return 1

    new_jobs = linkedin_export.dedupe_listings(jobs, known)
    sheet_rows = [
        linkedin_export.application_row(j, seeker_id=seeker_id, companies=companies) for j in new_jobs
    ]

    print(f"Scraped {len(jobs)} cards, {len(new_jobs)} new after dedupe (skipped {len(jobs) - len(new_jobs)} duplicates)")

    if args.dry_run:
        for row in sheet_rows:
            print(" | ".join(row[:7]))
        return 0

    if sheet_rows:
        sheets.append_rows("APPLICATIONS", sheet_rows)

    if args.import_companies:
        import datetime as dt

        today = dt.date.today().isoformat()
        for job, row in zip(new_jobs, sheet_rows):
            hr = row[6]
            verified = row[7]
            if verified != "Y" or not hr:
                continue
            sheets.append_row(
                "COMPANIES",
                [job.company, hr, today, "linkedin_export"],
            )

    if args.output:
        out = Path(args.output)
        if out.suffix.lower() == ".csv":
            _write_csv(out, APPLICATION_HEADERS, sheet_rows)
        else:
            try:
                _write_xlsx(out, APPLICATION_HEADERS, sheet_rows)
            except RuntimeError:
                _write_csv(out.with_suffix(".csv"), APPLICATION_HEADERS, sheet_rows)
                print(f"Wrote CSV backup (install openpyxl for xlsx): {out.with_suffix('.csv')}")

    print(f"Appended {len(sheet_rows)} row(s) to {tab}")
    if seeker_id:
        print(f"Run job process for {seeker_id}: admin → Run job process now (applies linkedin_lead rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
