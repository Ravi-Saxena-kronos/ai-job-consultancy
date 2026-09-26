# Production: email-only confirmations

Seekers are notified **only by email** (Resend, **Brevo**, or SMTP). There is **no automatic WhatsApp** in code.

| Event | How seeker is notified |
|-------|-------------------------|
| After Step 2 register | Email: registration received (if email provider configured) |
| After admin **Verify** | Email: payment verified + upload link |
| After Step 3 upload | Email: resume received |
| After job applied | Email: resume sent to company |

## Option A — No domain (Brevo + Gmail sender)

See **[BREVO-SETUP.md](BREVO-SETUP.md)**.

1. Verify your Gmail as a sender in Brevo.
2. Vercel: `BREVO_API_KEY`, `EMAIL_FROM=your@gmail.com`, `PUBLIC_BASE_URL`, redeploy.
3. Admin → **Test Resend setup** (works with Brevo too).

## Option B — Custom domain (Resend)

1. Domain verified in [Resend](https://resend.com)
2. Vercel: `RESEND_API_KEY`, `EMAIL_FROM=noreply@yourdomain.com`
3. `PUBLIC_BASE_URL` = your live URL
4. Redeploy

See [RESEND-SETUP.md](RESEND-SETUP.md).

## Provider selection

`EMAIL_PROVIDER=auto` (default): uses Resend if `RESEND_API_KEY` is set, else Brevo if `BREVO_API_KEY`, else SMTP if `SMTP_HOST`.

Set `EMAIL_PROVIDER=brevo` to force Brevo when both Resend and Brevo keys exist.

## WhatsApp in admin

**Manual testing only** — admin copies a message and sends from your phone.  
Use WhatsApp only as fallback if email is not configured.
