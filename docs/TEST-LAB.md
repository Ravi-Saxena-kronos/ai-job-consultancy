# Test lab (your resume, no production impact)

Use this to try tailored DOCX applies before onboarding paying seekers.

## Isolation from production

| Production | Test lab |
|------------|----------|
| `SEEKERS` tab, payments, `posts_remaining` | **`TESTING` tab only** |
| Cron **Run job process** | **Not used** — you call `/api/test/run` |
| `seeker_id` like `APS-…` | `TST-…` on applications |
| `JOB_APPLICATIONS.testing` empty | **`testing=Y`** |
| LinkedIn batch for real seekers | Rows with `testing=Y` or `TST-*` **skipped** |

Main site (`/`), register, upload, and admin verify flow are **unchanged**. With `TEST_LAB_ENABLED` unset/false, test APIs return **404**.

## Enable on Vercel

This repo sets **`TEST_LAB_ENABLED=true` in `vercel.json`** so Production always sees it after deploy (dashboard-only env vars sometimes do not reach the Python function).

To **turn off** test lab later, remove that block from `vercel.json` or set it to `false`, then redeploy.

Optional dashboard variables (still recommended):

```
TEST_LAB_SECRET=long-random-string   # optional; defaults to ADMIN_SECRET
TEST_LAB_MAX_APPLIES=3               # default cap per run
TEST_HR_REDIRECT=you@gmail.com       # recommended first: HR mail to you only
```

`/api/public_config` includes `test_lab`: `{ "env_key_present", "env_value_length", "enabled" }` for debugging.

1. Admin → **Init Google Sheet tabs** (creates **TESTING** tab).
2. On existing `JOB_APPLICATIONS`, add column **O** header: `testing` (if you added M/N earlier for tailoring).
3. Open `https://YOUR_APP.vercel.app/test.html`

## Backup

Before enabling in prod, keep a copy:

- Git tag: `backup-pre-test-lab`
- Archive: `backups/ai-job-consultancy-YYYYMMDD.tar.gz`

## Sheet: TESTING tab

| Column | Purpose |
|--------|---------|
| test_id | `TST-XXXXXXXX` |
| name, email, resume_url, target_role, domain, location | Your profile |
| max_applies | How many companies this run |
| status | submitted → running → completed / failed |
| notes | Run summary |

Applications still log on **JOB_APPLICATIONS** with `testing=Y` for audit.
