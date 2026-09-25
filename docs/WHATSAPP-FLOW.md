# Testing only — manual WhatsApp (not production)

Production uses **email only** — see `PRODUCTION-EMAIL.md`.

# Track 1 — WhatsApp (no Resend domain)

## Admin (you)

1. Open https://ai-job-consultancy.vercel.app/admin.html
2. Unlock with `ADMIN_SECRET`
3. Match UTR in Amazon Pay → **Verify**
4. Copy the **WhatsApp message** box → paste to seeker on WhatsApp  
   (Or **WhatsApp** button if already verified)
5. Optional: **Open WhatsApp (web)** with message pre-filled

## Seeker (e.g. Priti)

1. Pay ₹99 → Step 2 register on site
2. Wait for your WhatsApp with upload link
3. Open link → **Step 3** → resume + role (same email as registration)

## Priti now (manual)

If she is already pending/verified in sheet:

1. Admin → **Verify** (if still pending)
2. Copy WhatsApp text → send to her number
3. Link format: `https://ai-job-consultancy.vercel.app/?seeker_id=APS-XXXX#upload`

No `RESEND_API_KEY` required for this flow.
