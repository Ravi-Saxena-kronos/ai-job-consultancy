#!/usr/bin/env python3
"""List Google Sheet tab titles and gids (for LINKEDIN_JOBS_GID / SHEET_APPLICATIONS)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lib.config import env  # noqa: E402
from lib.sheets import _get_sheets_service, _sid  # noqa: E402


def main() -> int:
    if not env("GOOGLE_SHEET_ID"):
        print("error: set GOOGLE_SHEET_ID in .env")
        return 1
    meta = _get_sheets_service().spreadsheets().get(spreadsheetId=_sid()).execute()
    print(f"Spreadsheet: {_sid()}\n")
    for sheet in meta.get("sheets", []):
        props = sheet.get("properties", {})
        title = props.get("title", "")
        gid = props.get("sheetId", "")
        print(f"  gid={gid}  tab={title}")
    print("\nFor LinkedIn export, set in .env:")
    print("  SHEET_APPLICATIONS=JOB_APPLICATIONS")
    print("  (or LINKEDIN_JOBS_GID=<gid for JOB_APPLICATIONS tab>)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
