# Deploy AI Job Consultancy on Vercel

## 1. Google Sheet

Create spreadsheet with tabs `SEEKERS`, `JOB_APPLICATIONS`, `COMPANY_VERIFIED` — headers in `docs/SHEET-COLUMNS.md`.

Google Cloud → Service account → JSON key → share sheet with `client_email` as Editor.

## 2. Vercel project

1. [vercel.com/new](https://vercel.com/new) → import Git repo  
2. **Root Directory:** `.` (this repo) or `ai-job-consultancy` if monorepo  
3. **Framework Preset:** **Other** (repo sets `"framework": null` in `vercel.json` — do **not** pick FastAPI/Python preset or build fails with “No python entrypoint”)  
4. Environment variables from `.env.example` (Production):

| Variable | Required |
|----------|----------|
| GOOGLE_SERVICE_ACCOUNT_JSON | yes (single-line JSON) |
| GOOGLE_SHEET_ID | yes |
| RESEND_API_KEY | yes |
| EMAIL_FROM | yes |
| ADZUNA_APP_ID / ADZUNA_APP_KEY | yes for job search |
| ADMIN_SECRET | yes |
| CRON_SECRET | yes |
| UPI_VPA | default 8595066768@amazonpay |

5. Deploy

## 3. Smoke test

- `GET https://YOUR.vercel.app/api/health`  
- `GET https://YOUR.vercel.app/api/public_config`  
- Open `/` — pay UPI → register form  

## 4. Verify first payment (manual)

After seeker pays ₹99 to Amazon Pay UPI:

```bash
curl -X POST "https://YOUR.vercel.app/api/admin/verify_payment" \
  -H "Authorization: Bearer YOUR_ADMIN_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"seeker_id":"APS-XXXXXX","email":"seeker@example.com","utr":"..."}'
```

## 5. Cron

Vercel **Hobby** allows **one cron per day** — default `30 2 * * *` (08:00 IST). Pro plan can use more frequent schedules. Test manually:

```bash
curl "https://YOUR.vercel.app/api/cron/process" \
  -H "Authorization: Bearer YOUR_CRON_SECRET"
```

## Local checks (no deploy)

```bash
cd ai-job-consultancy
python3 tests/test_hr_verify.py
python3 -m compileall lib api
```
