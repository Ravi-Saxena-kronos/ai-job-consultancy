# AI Job Consultancy (email-only) + AI Resume Post backend

**Code scaffold:** Vercel + Google Sheets + Adzuna + Resend email + **Amazon Pay UPI** (`8595066768@amazonpay`, env `UPI_VPA`).

Setup: **`SETUP.md`** · Deploy: **`DEPLOY.md`**  
Sheet columns: **`docs/SHEET-COLUMNS.md`**

```bash
cd ai-job-consultancy && python3 tests/test_hr_verify.py && python3 -m compileall lib api
```

Planning and MVP scaffold for an **email-only** job seeker service:

- Registration fee (e.g. ₹99) via payment gateway
- Resume upload + optional paid packages (5 / 10 / 15 / 20 / 30 company outreach)
- **Backend worker** matches resume to roles and sends applications **only where legally allowed**
- Job seeker gets **email notifications** for each action (no phone in product)

## Read first (legal / platform rules)

| Idea | Reality |
|------|---------|
| Bot search LinkedIn and auto-apply | **Violates [LinkedIn User Agreement](https://www.linkedin.com/legal/user-agreement)**. Accounts get banned; do not build this as core tech. |
| Upload resume “into” a company without their portal | Usually **impossible** unless they expose careers email or ATS API. |
| Mass unsolicited email to HR | **Spam / IT Act risk** and harms your domain reputation. |

**Working alternative:** AI **finds** matching openings (public job feeds, career pages, Naukri/Indeed where API/partner exists), **prepares** tailored application pack, then either (a) **emails the company only on published careers addresses** with seeker consent, or (b) **emails the seeker** “apply here” links + attached optimized resume. Track everything by email.

## Repo layout

```
ai-job-consultancy/
  README.md                 ← this file
  ARCHITECTURE.md           ← full technical model
  docs/
    email-templates/        ← seeker + audit trail copy
  web/                      ← future: seeker upload + pay (static/Vercel)
  worker/                   ← future: match + queue + send (Python stdlib-friendly)
```

## Guides (DOCX)

Generate:

```bash
python3 ai-job-consultancy/build_consultancy_guide.py
```

Output: `AI-Job-Consultancy-Full-Working-Model.docx`

## MVP order of build

1. Landing page + Razorpay ₹99 + resume upload to private storage  
2. Email: welcome + receipt + “we received your resume”  
3. Admin: list seekers, mark package (5/10/15 posts)  
4. Worker: parse resume → match → **curated apply queue** → send via SES/SendGrid  
5. Email seeker per company: “Applied to X via careers@x.com” or “Apply yourself: link”  

Publicity checklist is in the DOCX (Product Hunt, GitHub, Dev.to, etc.) — not LinkedIn automation.
