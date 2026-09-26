# LinkedIn job export (local)

Semi-automated: **you** log in to LinkedIn in a real browser; the script searches, collects listings, and appends to your **JOB_APPLICATIONS** Google Sheet tab.

Not deployed on Vercel (Playwright + your session stay on your laptop).

## Setup

Ubuntu/Debian blocks `pip install` on system Python (PEP 668). Use a **venv** in this folder:

```bash
cd ai-job-consultancy
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-linkedin-export.txt
playwright install chromium
```

If `python3 -m venv` fails, install once: `sudo apt install python3-venv python3-full`

`.env` (same as production):

| Variable | Example |
|----------|---------|
| `GOOGLE_SHEET_ID` | `1qOE-FyC9YAtFhmawynXyTbSk5uN7aoVKkyRdjcUr7oI` |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | service account key (one line) |
| `LINKEDIN_JOBS_GID` | `2126827446` (optional; resolves tab title for JOB_APPLICATIONS) |

Share the spreadsheet with the service account email as **Editor**.

Set the same `GOOGLE_SHEET_ID` and `LINKEDIN_JOBS_GID` on **Vercel** so cron/admin apply sees the same rows.

## Run

```bash
source .venv/bin/activate   # if not already active
python scripts/linkedin_jobs_export.py \
  --seeker-id APS-XXXX \
  --max-jobs 30 \
  --fetch-descriptions
```

Or explicit search:

```bash
python scripts/linkedin_jobs_export.py \
  --role "Python developer" \
  --location "Delhi" \
  --seeker-id APS-XXXX
```

1. Chromium opens → log in to LinkedIn if prompted.
2. Press **Enter** in the terminal when job results are visible.
3. Script scrolls, dedupes by `job_url`, appends new rows.

Flags:

- `--dry-run` — print rows, do not write sheet
- `--import-companies` — also append verified `hr_email` to COMPANY_VERIFIED
- `--output data/backup.csv` — local backup
- `--profile-dir` — default `data/linkedin-browser-profile` (login reused)

## Sheet columns

Same as [SHEET-COLUMNS.md](SHEET-COLUMNS.md) **JOB_APPLICATIONS**.

| status | Meaning |
|--------|---------|
| `linkedin_lead` | HR/careers email found; cron can apply |
| `skipped_no_email` | No verified email |

## After export

1. Seeker must have resume uploaded and `posts_remaining` > 0.
2. **Admin → Run job process now** (or daily cron) applies `linkedin_lead` rows: emails HR + notifies candidate.

## Limits

- LinkedIn rarely shows personal HR emails; many rows stay `skipped_no_email`.
- LinkedIn may change HTML — update selectors in `lib/linkedin_scrape.py` if zero jobs.
- Do not run headless password bots; manual login only.
