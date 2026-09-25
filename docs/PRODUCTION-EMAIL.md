# Production: email-only confirmations

Seekers are notified **only by email** (Resend). There is **no automatic WhatsApp** in code.

| Event | How seeker is notified |
|-------|-------------------------|
| After Step 2 register | Email: registration received (if Resend configured) |
| After admin **Verify** | Email: payment verified + upload link |
| After Step 3 upload | Email: resume received |
| After job applied | Email: resume sent to company |

## Required for production

1. Domain verified in [Resend](https://resend.com)
2. Vercel: `RESEND_API_KEY`, `EMAIL_FROM=noreply@yourdomain.com`
3. `PUBLIC_BASE_URL` = your live URL
4. Redeploy

## WhatsApp in admin

**Manual testing only** — admin copies a message and sends from your phone.  
Disable reliance on WhatsApp once email works; you can ignore the WhatsApp box in admin.

## Testing without domain

Use admin **Verify** + copy WhatsApp text, or Gmail manually to seeker email.  
Do not treat WhatsApp as the product channel for launch.
