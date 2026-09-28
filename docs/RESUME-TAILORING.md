# Resume tailoring (per job)

When batch apply runs (cron or admin **Run batch**), each send:

1. Downloads the seeker resume from `resume_url` (public Google Drive or PDF).
2. Tailors text with OpenAI (`OPENAI_API_KEY`, optional `OPENAI_MODEL`, default `gpt-4o-mini`). If the key is missing, a keyword-only **Skills aligned with this role** block is added instead.
3. Builds a Word file (`python-docx`).
4. Emails HR with the DOCX attached (no resume link in the body).
5. Emails the candidate the **same** DOCX for their records.

## Sheet audit columns (JOB_APPLICATIONS)

| Column | Meaning |
|--------|---------|
| `tailored_sent` | `Y` when a tailored DOCX was sent |
| `docx_filename` | Attachment name, e.g. `Resume_Name_Company_APP123.docx` |

Add these headers on existing spreadsheets (columns M and N after `hr_message_id`), or run **Init Google Sheet tabs** on a new sheet via `scripts/setup_sheet.py` / admin.

## Vercel

Set `OPENAI_API_KEY` in project environment variables. Redeploy after changing `requirements.txt` (`pypdf`, `python-docx`).

## Resume link

Drive links must be **Anyone with the link** view. PDF URLs must be directly fetchable.
