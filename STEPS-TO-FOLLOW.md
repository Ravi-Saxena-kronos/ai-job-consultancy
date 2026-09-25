# AI Job Consultancy — all steps to follow

**Your rules**

1. Email **HR** only when `hr_email` is **verified enough** (see Step 11).
2. Email **candidate** only when HR email was used and resume was sent — **no** “apply link” or other outreach emails if HR email is missing.
3. On the app: **“We do not guarantee HR contact or selection.”**

---

## Phase 0 — Decisions (Day 1)

| Step | Action |
|------|--------|
| 0.1 | Choose brand name (e.g. ApplyDesk). |
| 0.2 | Use free URL `yourname.vercel.app` or buy `.in` domain (~₹500+/year). |
| 0.3 | Decide packages: ₹99 registration + POST-5 / 10 / 15 (prices later). |
| 0.4 | Niche first: e.g. “IT 0–3 yrs NCR”, “Accountant Delhi”, etc. |

---

## Phase 1 — Business & legal (Week 1)

| Step | Action |
|------|--------|
| 1.1 | Open bank account (if needed) for Razorpay settlements. |
| 1.2 | Register business (proprietorship minimum; Pvt Ltd if scaling). |
| 1.3 | Apply **GST** when turnover requires; mention on invoice if registered. |
| 1.4 | Write **Privacy Policy** (resume storage, retention, deletion). |
| 1.5 | Write **Terms of Service**: consent to email employers; **no guarantee** of HR contact, interview, or selection. |
| 1.6 | Write **Refund policy** (e.g. ₹99 non-refundable after resume processing). |
| 1.7 | Add checkbox at signup: “I authorize submission of my resume to employers when a verified careers email is available.” |

**App honesty line (footer + Terms + after payment):**

> We do not guarantee HR contact or selection.

---

## Phase 2 — Email & domain (Week 1)

| Step | Action |
|------|--------|
| 2.1 | Create **Google Workspace** or use domain host email: `noreply@`, `apply@`, `support@`. |
| 2.2 | Sign up **Resend** or **Amazon SES**. |
| 2.3 | Add **SPF**, **DKIM**, **DMARC** on domain (required so mail is not spam). |
| 2.4 | Send test mail to Gmail/Yahoo; check inbox not spam. |

**Emails you will send**

| When | To | Content |
|------|-----|---------|
| After ₹99 pay | Candidate | Receipt + upload link |
| After resume upload | Candidate | “Resume received” |
| After HR apply only | HR | Cover letter + resume |
| After HR apply only | Candidate | “Resume sent to [Company] – [Title]” |
| Missing HR email | Candidate | **Nothing** (your rule) |

---

## Phase 3 — Private spreadsheets (Week 1–2)

Use **Google Sheets** (only your Google account + service account). Export to Excel anytime.

### Sheet 1: `SEEKERS` (one row per job seeker)

| Column | Example |
|--------|---------|
| seeker_id | APS-1001 |
| email | user@gmail.com |
| paid_reg | Y |
| payment_id | pay_xxx |
| resume_url | (private link) |
| domain | IT / Sales / Accounts |
| experience_years | 2 |
| target_role | Java Developer |
| location | Delhi NCR |
| posts_remaining | 10 |
| status | active / completed |
| created_at | date |

### Sheet 2: `JOB_APPLICATIONS` (many rows per seeker)

| Column | Example |
|--------|---------|
| application_id | APP-5001 |
| seeker_id | APS-1001 |
| title | Java Developer |
| company | ABC Pvt Ltd |
| location | Gurgaon |
| job_url | https://… |
| hr_email | careers@abc.com |
| email_verified | Y / N |
| verification_method | company_csv / jd_parse / mx_check |
| status | pending / applied / skipped_no_email |
| applied_at | datetime |
| hr_message_id | (for audit) |

### Sheet 3: `COMPANY_VERIFIED` (your master list — improves HR hit rate)

| Column | Example |
|--------|---------|
| company_name | ABC Pvt Ltd |
| hr_email | careers@abc.com |
| verified_on | date |
| source | manual / website |

---

## Phase 4 — Payments (Week 2)

| Step | Action |
|------|--------|
| 4.1 | Create **Razorpay** business account; complete KYC. |
| 4.2 | Create product **Registration ₹99**. |
| 4.3 | Create products **POST-5, POST-10, POST-15** (amounts when ready). |
| 4.4 | Test mode: fake payment → webhook → mark seeker paid in sheet. |
| 4.5 | Live mode only after website + Terms are live. |

---

## Phase 5 — Job discovery API (Week 2)

| Step | Action |
|------|--------|
| 5.1 | Register at [Adzuna API](https://developer.adzuna.com/) → `app_id`, `app_key`. |
| 5.2 | Test India search: `jobs/in/search/1?what=java+developer&where=Delhi`. |
| 5.3 | Store only: title, company, location, job_url, description, created. |
| 5.4 | Respect API quota; cache results; do not hammer API. |

**Do not** use LinkedIn/Naukri login bots.

---

## Phase 6 — Website on Vercel (Week 2–3)

| Step | Action |
|------|--------|
| 6.1 | Push `ai-job-consultancy/web` to GitHub. |
| 6.2 | Import repo in **Vercel**; deploy. |
| 6.3 | Pages: Home, Plans, Terms, Privacy, Upload (after pay). |
| 6.4 | Show all plans + disclaimer: **We do not guarantee HR contact or selection.** |
| 6.5 | **Email-only** login (magic link); no phone field. |
| 6.6 | Environment variables: Razorpay keys, Resend key, Google service account JSON, Adzuna keys, storage URL. |

---

## Phase 7 — Resume upload & categorization (Week 3)

| Step | Action |
|------|--------|
| 7.1 | After ₹99, allow PDF upload to **private storage** (Supabase/S3/Vercel Blob). |
| 7.2 | Run AI parse (or rules): skills, years, domain, suggested role. |
| 7.3 | Append row to **SEEKERS** sheet automatically. |
| 7.4 | Email candidate: resume received (not an “applied” mail). |

---

## Phase 8 — HR email verification (critical — Week 3)

Only these count as **verified enough to email HR**:

| Rule | Accept? |
|------|---------|
| Email in **COMPANY_VERIFIED** sheet (you checked website) | **Yes** |
| Email in job description matching `careers@`, `jobs@`, `recruitment@`, `hr@` **and** domain matches company name | **Maybe** — optional MX check |
| **MX record exists** for domain (DNS lookup) | Required if not in COMPANY_VERIFIED |
| Random `info@gmail.com` in JD | **No** |
| Guessed `hr@company.com` without proof | **No** |

If **not verified** → row status `skipped_no_email` → **no email to HR, no email to candidate**.

Optional: run **MX lookup** in automation (stdlib DNS or API) before send.

---

## Phase 9 — Automation loop (Week 4)

Run on **Vercel Cron** (e.g. every 15 minutes) or daily:

```
FOR each seeker in SEEKERS where posts_remaining > 0 and status = active:
  1. Build Adzuna query from target_role + location + experience band
  2. FOR each job result (until posts_remaining = 0):
       a. Dedupe: skip if same company+title in last 90 days for this seeker
       b. Resolve hr_email: COMPANY_VERIFIED first, else parse JD
       c. IF NOT verified enough → write JOB_APPLICATIONS row skipped_no_email → CONTINUE (no candidate email)
       d. IF verified → send email to HR (resume + cover letter)
       e. Update row status = applied
       f. Decrement posts_remaining
       g. Email candidate ONLY NOW: "Resume sent to [Company] for [Title]"
  3. IF posts_remaining = 0 → seeker status = completed
```

**You** monitor **JOB_APPLICATIONS** in Sheet — candidates do not get mail for skipped rows.

---

## Phase 10 — Email templates (Week 4)

| Template | To |
|----------|-----|
| registration_receipt | Candidate |
| resume_received | Candidate |
| hr_application | HR (with PDF resume) |
| candidate_applied_confirmation | Candidate (only after HR send) |

Samples: `ai-job-consultancy/docs/email-templates/`

---

## Phase 11 — Testing before launch (Week 4)

| Step | Action |
|------|--------|
| 11.1 | Pay ₹99 test; upload test PDF. |
| 11.2 | Confirm **SEEKERS** row created. |
| 11.3 | Add fake job with **verified** test HR (your own inbox). |
| 11.4 | Run cron once → HR mail received → candidate notification received. |
| 11.5 | Add job with **no** HR email → confirm **no** candidate mail; sheet shows `skipped_no_email`. |
| 11.6 | Check spam score on all templates. |

---

## Phase 12 — Go live (Week 5)

| Step | Action |
|------|--------|
| 12.1 | Razorpay live keys on Vercel. |
| 12.2 | Remove test data from sheets. |
| 12.3 | Add 20–50 rows to **COMPANY_VERIFIED** for your niche. |
| 12.4 | Soft launch: 10 real seekers; you watch sheet daily. |
| 12.5 | Fix bounces; never send to invalid HR again. |

---

## Phase 13 — Publicity (after live)

| Step | Channel |
|------|---------|
| 13.1 | Google Search Console — submit sitemap |
| 13.2 | GitHub — open landing/toolkit repo with link to service |
| 13.3 | Product Hunt / Dev.to / Reddit (follow rules) |
| 13.4 | Your LinkedIn — manual posts (no automation on LinkedIn) |

---

## Phase 14 — What you do ongoing

| Daily | Weekly |
|-------|--------|
| Open **JOB_APPLICATIONS** sheet | Add verified companies to **COMPANY_VERIFIED** |
| Check failed/bounced HR emails | Review Adzuna quota |
| Reply **support@** within 24h | Adjust role keywords per niche |

---

## Checklist summary (print)

- [ ] Terms + no-guarantee disclaimer live  
- [ ] Razorpay ₹99 working  
- [ ] Receipt + resume received emails  
- [ ] Three Google Sheets (Seekers, Applications, Company verified)  
- [ ] Adzuna API connected  
- [ ] HR verification rules coded  
- [ ] Candidate email **only** after HR send  
- [ ] Vercel cron running  
- [ ] SPF/DKIM/DMARC OK  

---

## Repo files

| File | Purpose |
|------|---------|
| `ai-job-consultancy/STEPS-TO-FOLLOW.md` | This document |
| `AI-Job-Consultancy-Steps-To-Follow.docx` | Downloadable (run builder below) |
| `ai-job-consultancy/build_steps_docx.py` | Regenerate DOCX |

```bash
python3 ai-job-consultancy/build_steps_docx.py
```
