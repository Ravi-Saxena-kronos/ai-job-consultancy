# Brevo email — no domain required

Use this when you **do not own a domain** but want automated emails to candidates (Gmail, etc.).

## 1. Create Brevo account

1. Sign up at [brevo.com](https://www.brevo.com) (free tier includes daily sending limits — check their pricing page).
2. **Settings → SMTP & API → API keys** → create a key → copy `xkeysib-...`.

## 2. Verify your sender (Gmail is fine)

1. **Senders & IP → Senders** → Add a sender.
2. Use the **same Gmail** you want candidates to see (e.g. `yourname@gmail.com`).
3. Complete Brevo’s verification email to that inbox.

You do **not** need to buy a domain for this path.

## 3. Vercel environment variables

Remove or leave empty `RESEND_API_KEY` if you want Brevo only (auto mode picks Resend first when both are set).

| Variable | Example |
|----------|---------|
| `EMAIL_FROM` | `yourname@gmail.com` (must match verified sender) |
| `EMAIL_FROM_NAME` | `AI Job Consultancy` (optional) |
| `BREVO_API_KEY` | `xkeysib-...` |
| `EMAIL_PROVIDER` | `brevo` (optional; auto works if only Brevo is set) |
| `PUBLIC_BASE_URL` | `https://ai-job-consultancy.vercel.app` |
| `ADMIN_NOTIFY_EMAIL` | your Gmail (for admin alerts + test email default) |

Redeploy after saving env vars.

## 4. Smoke test

**Local (fastest):**

```bash
cd ai-job-consultancy
# .env with BREVO_API_KEY, EMAIL_FROM, EMAIL_PROVIDER=brevo
python3 scripts/test_brevo_email.py ravisaxenaa786@gmail.com
```

**On Vercel (after redeploy):**

1. Open `/admin.html` → unlock with `ADMIN_SECRET`.
2. Click **Test Resend setup** (uses Brevo when configured).
3. Check inbox and **Spam**; if admin shows a long error (not JSON), open **Vercel → Logs** for that request.

Common fixes: `EMAIL_FROM` must match verified Brevo sender; unset `RESEND_API_KEY` or set `EMAIL_PROVIDER=brevo`.

## Alternative: Brevo SMTP (same account)

If the HTTP API is blocked, set:

| Variable | Value |
|----------|--------|
| `EMAIL_PROVIDER` | `smtp` |
| `SMTP_HOST` | `smtp-relay.brevo.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | your Brevo login email |
| `SMTP_PASSWORD` | Brevo SMTP key (not your Gmail password) |
| `EMAIL_FROM` | verified sender address |

## Limits

- Free tier caps apply; high volume needs a paid plan.
- Mail from `@gmail.com` may land in Promotions/Spam more often than `noreply@yourdomain.com`.
- When you later buy a domain, you can switch to Resend with `EMAIL_FROM=noreply@yourdomain.com`.
