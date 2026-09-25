# Setup (do not run until you are ready)

You asked for code only — **no deploy or live execution** from the agent. Follow these steps yourself when ready.

## 1. UPI / Amazon Pay wallet

Default wallet on site: **`8595066768@amazonpay`** (override with env `UPI_VPA` on Vercel).

Job seekers pay ₹99 via GPay / PhonePe / Paytm → **Pay to UPI ID** → paste wallet → pay.

## 2. Google Sheet

1. Create one spreadsheet with tabs: `SEEKERS`, `JOB_APPLICATIONS`, `COMPANY_VERIFIED`
2. Add header rows from `docs/SHEET-COLUMNS.md`
3. Google Cloud → Service Account → JSON key
4. Share the sheet with the service account email (Editor)
5. Copy spreadsheet ID into `GOOGLE_SHEET_ID`
6. Paste JSON into `GOOGLE_SERVICE_ACCOUNT_JSON` (one line on Vercel)

## 3. Adzuna

1. Register at https://developer.adzuna.com/
2. Set `ADZUNA_APP_ID` and `ADZUNA_APP_KEY`

## 4. Email (Resend)

1. Verify domain → `RESEND_API_KEY`, `EMAIL_FROM`

## 5. Secrets

Copy `.env.example` → `.env` locally. On Vercel set the same variables plus:

- `ADMIN_SECRET` — for verify payment API
- `CRON_SECRET` — must match Vercel cron Authorization header

## 6. Deploy on Vercel

1. New project → root directory **`ai-job-consultancy`**
2. Add env vars
3. Deploy (you run this — not automated here)

## 7. After deploy — payment flow (Amazon Pay UPI)

1. Seeker pays ₹99 to `8595066768@amazonpay` (or your `UPI_VPA`)
2. Seeker submits form → `POST /api/register` → Sheet `payment_status=pending`
3. You confirm UPI in bank app
4. `POST /api/admin/verify_payment` with header `Authorization: Bearer YOUR_ADMIN_SECRET`:

```json
{ "seeker_id": "APS-ABC123", "email": "user@example.com", "utr": "..." }
```

5. Seeker uploads resume → `POST /api/upload`
6. Cron `/api/cron/process` runs matching (every 6h in vercel.json)

## 8. Candidate email rule

- Email to candidate **only** when HR email was verified and send succeeded
- `skipped_no_email` → no candidate mail

## API routes

| Route | Method |
|-------|--------|
| `/api/register` | POST |
| `/api/upload` | POST |
| `/api/admin/verify_payment` | POST + ADMIN_SECRET |
| `/api/cron/process` | GET + CRON_SECRET |

Static site: `public/index.html`
