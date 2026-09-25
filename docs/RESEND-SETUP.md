# Resend — why “sent OK” but Gmail does not receive

## Most common cause

**`EMAIL_FROM` is not on a verified domain.**

| EMAIL_FROM | Can send to saxenapj@gmail.com? |
|------------|----------------------------------|
| `onboarding@resend.dev` | **Only** the email you used to sign up for Resend |
| `noreply@yourdomain.com` (domain verified in Resend) | **Yes** |

The app calls Resend; Resend returns **200 + id**. Mail still may **not deliver** to arbitrary Gmail until the domain is verified.

## Fix (production)

1. [resend.com](https://resend.com) → **Domains** → Add your domain.
2. Add DNS records (TXT, MX, etc.) at your domain host.
3. Wait until status **Verified**.
4. Vercel env:
   - `EMAIL_FROM=noreply@yourdomain.com` (must match verified domain)
   - `RESEND_API_KEY=re_...`
5. **Redeploy**.

## Check delivery

1. Resend → **Emails** — find message by id (admin shows `resend_id`).
2. Status: **Delivered**, **Bounced**, or **Failed** (click for reason).
3. Seeker checks **Spam / Promotions**.

## Admin tools

- **Test Resend setup** — sends one test mail and shows Resend id.
- **Resend email to seeker** → OK = payment verified template.

## Temporary workaround (no domain yet)

- Tell seeker the upload link manually from admin / sheet Seeker ID.
- Or verify payment in admin and share:  
  `https://ai-job-consultancy.vercel.app/?seeker_id=APS-XXXX#upload`
