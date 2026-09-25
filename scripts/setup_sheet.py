#!/usr/bin/env python3
"""One command: create SEEKERS / JOB_APPLICATIONS / COMPANY_VERIFIED tabs + headers."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lib import sheets  # noqa: E402


def main() -> int:
    tabs = sheets.ensure_workbook_tabs()
    print("Sheet ready:", tabs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
