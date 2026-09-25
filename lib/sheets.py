"""Google Sheets read/append for SEEKERS, JOB_APPLICATIONS, COMPANY_VERIFIED."""

from __future__ import annotations

from typing import Any, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build

from .config import env, google_service_account_info

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
_sheets_api = None


def _get_sheets_service():
    global _sheets_api
    if _sheets_api is None:
        creds = service_account.Credentials.from_service_account_info(
            google_service_account_info(), scopes=SCOPES
        )
        _sheets_api = build("sheets", "v4", credentials=creds, cache_discovery=False)
    return _sheets_api


def _sid() -> str:
    sheet_id = env("GOOGLE_SHEET_ID")
    if not sheet_id:
        raise RuntimeError("GOOGLE_SHEET_ID is not set")
    return sheet_id


_TAB_ENV = {
    "SEEKERS": ("SHEET_SEEKERS", "SEEKERS"),
    "APPLICATIONS": ("SHEET_APPLICATIONS", "JOB_APPLICATIONS"),
    "COMPANIES": ("SHEET_COMPANIES", "COMPANY_VERIFIED"),
}


def sheet_name(tab: str) -> str:
    key, default = _TAB_ENV.get(tab, (tab, tab))
    return env(key, default)


def append_row(tab: str, values: list[Any]) -> None:
    name = sheet_name(tab) if tab in _TAB_ENV else tab
    body = {"values": [values]}
    _get_sheets_service().spreadsheets().values().append(
        spreadsheetId=_sid(),
        range=f"{name}!A:Z",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body=body,
    ).execute()


def read_all(tab: str) -> list[list[str]]:
    name = sheet_name(tab) if tab in _TAB_ENV else tab
    result = (
        _get_sheets_service()
        .spreadsheets()
        .values()
        .get(spreadsheetId=_sid(), range=f"{name}!A:Z")
        .execute()
    )
    return result.get("values") or []


def rows_as_dicts(tab: str) -> list[dict[str, str]]:
    rows = read_all(tab)
    if not rows:
        return []
    headers = [str(h).strip().lower().replace(" ", "_") for h in rows[0]]
    out = []
    for row in rows[1:]:
        padded = row + [""] * (len(headers) - len(row))
        out.append({headers[i]: padded[i] for i in range(len(headers))})
    return out


def update_row(tab: str, row_index: int, values: list[Any]) -> None:
    """row_index is 1-based sheet row (including header)."""
    name = sheet_name(tab) if tab in _TAB_ENV else tab
    end_col = chr(ord("A") + max(len(values) - 1, 0))
    cell_range = f"{name}!A{row_index}:{end_col}{row_index}"
    _get_sheets_service().spreadsheets().values().update(
        spreadsheetId=_sid(),
        range=cell_range,
        valueInputOption="USER_ENTERED",
        body={"values": [values]},
    ).execute()


def find_row_index(tab: str, col: str, equals: str) -> Optional[int]:
    """Return 1-based row index of first data row where column col matches."""
    rows = read_all(tab)
    if not rows:
        return None
    headers = [str(h).strip().lower().replace(" ", "_") for h in rows[0]]
    try:
        idx = headers.index(col.lower())
    except ValueError:
        return None
    want = equals.strip().lower()
    for i, row in enumerate(rows[1:], start=2):
        if idx < len(row) and str(row[idx]).strip().lower() == want:
            return i
    return None


def ensure_workbook_tabs() -> dict[str, str]:
    """Create missing tabs and write header row if sheet is empty. Returns tab key → sheet title."""
    from . import sheet_schema

    sid = _sid()
    meta = _get_sheets_service().spreadsheets().get(spreadsheetId=sid).execute()
    existing = {s["properties"]["title"] for s in meta.get("sheets", [])}
    requests = []
    for tab_key in sheet_schema.TAB_SPECS:
        title = sheet_name(tab_key)
        if title not in existing:
            requests.append({"addSheet": {"properties": {"title": title}}})
    if requests:
        _get_sheets_service().spreadsheets().batchUpdate(
            spreadsheetId=sid, body={"requests": requests}
        ).execute()

    report: dict[str, str] = {}
    for tab_key, headers in sheet_schema.TAB_SPECS.items():
        title = sheet_name(tab_key)
        report[tab_key] = title
        rows = read_all(tab_key) if title in existing or requests else []
        if not rows:
            _get_sheets_service().spreadsheets().values().update(
                spreadsheetId=sid,
                range=f"{title}!A1",
                valueInputOption="USER_ENTERED",
                body={"values": [headers]},
            ).execute()
        elif rows[0] != headers:
            # Leave data as-is; only fill headers when completely empty workbook row
            first = [str(c).strip().lower().replace(" ", "_") for c in rows[0]]
            want = [h.lower() for h in headers]
            if first != want and len(rows) == 1 and not any(str(c).strip() for c in rows[0]):
                update_row(tab_key, 1, headers)
    return report


def find_verified_company_email(company: str, companies: Optional[list[dict]] = None) -> Optional[str]:
    companies = companies if companies is not None else rows_as_dicts("COMPANIES")
    needle = company.strip().lower()
    for row in companies:
        name = (row.get("company_name") or row.get("company") or "").strip().lower()
        if name and (name in needle or needle in name):
            email = (row.get("hr_email") or row.get("email") or "").strip()
            if email:
                return email
    return None
