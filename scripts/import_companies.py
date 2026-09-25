#!/usr/bin/env python3
"""Append companies from CSV: company_name,hr_email[,verified_on,source]"""

from __future__ import annotations

import csv
import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lib import sheets  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_companies.py companies.csv")
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print("File not found:", path)
        return 2
    today = dt.date.today().isoformat()
    count = 0
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("company_name") or row.get("company") or "").strip()
            email = (row.get("hr_email") or row.get("email") or "").strip()
            if not name or not email:
                continue
            verified = (row.get("verified_on") or today).strip()
            source = (row.get("source") or "csv_import").strip()
            sheets.append_row("COMPANIES", [name, email, verified, source])
            count += 1
    print(f"Imported {count} companies")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
