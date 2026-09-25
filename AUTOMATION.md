# Automation — minimal manual work

## Fully automatic (after one-time setup)

| Step | What runs |
|------|-----------|
| Job matching + HR email | Vercel cron every 6 hours → `/api/cron/process` |
| Online ₹99 payment | Razorpay checkout → `/api/payment/confirm` (instant) + webhook backup |
| Payment verified email | Upload link with `seeker_id` |
| New UPI registration | Seeker gets “received” email; you get `ADMIN_NOTIFY_EMAIL` if set |
| Google Sheet structure | `python scripts/setup_sheet.py` or Admin → **Init Google Sheet tabs** |

## Semi-automatic (seconds, not curl)

| Step | Action |
|------|--------|
| Amazon Pay UPI + UTR | Open `/admin.html` → **Verify** (one click per seeker) |
| Run jobs early | Admin → **Run job process now** |
| Import companies | `python scripts/import_companies.py data/companies.csv` |

## One-time manual (cannot skip)

1. Google Cloud service account + share Sheet with service account email  
2. Vercel project (root `ai-job-consultancy`), paste env from `.env.example`  
3. `python scripts/check_env.py` locally before deploy  
4. Resend domain verify, Adzuna keys  
5. **Razorpay (recommended):** Dashboard → Webhook URL `https://YOUR_DOMAIN/api/payment/razorpay_webhook`, event `payment.captured`, secret → `RAZORPAY_WEBHOOK_SECRET`  

Amazon Pay wallet has **no public API** to auto-match UTR — Razorpay removes that step; UPI wallet stays as fallback.

## Env for automation

```env
PUBLIC_BASE_URL=https://your-app.vercel.app
ADMIN_NOTIFY_EMAIL=you@gmail.com
RAZORPAY_KEY_ID=rzp_live_...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...
```

Leave Razorpay vars empty to keep Amazon Pay UPI only.

## Quick deploy checklist

```sh
cd ai-job-consultancy
cp .env.example .env   # fill values
python3 scripts/check_env.py
python3 scripts/setup_sheet.py
python3 -m compileall lib api
# vercel deploy (root directory = ai-job-consultancy)
```

Then visit `/admin.html` once to confirm pending list loads.
