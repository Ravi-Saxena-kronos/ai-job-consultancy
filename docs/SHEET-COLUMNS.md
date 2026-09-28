# Google Sheet tabs (create one spreadsheet, share with service account email)

## SEEKERS (header row 1)

| Column | Header |
|--------|--------|
| A | seeker_id |
| B | email |
| C | name |
| D | paid_reg |
| E | utr |
| F | payment_status |
| G | resume_url |
| H | domain |
| I | experience_years |
| J | target_role |
| K | location |
| L | posts_remaining |
| M | status |
| N | created_at |

`payment_status`: pending | verified  
`status`: pending_payment | pending_resume | active | completed

## JOB_APPLICATIONS

| A | application_id |
| B | seeker_id |
| C | title |
| D | company |
| E | location |
| F | job_url |
| G | hr_email |
| H | email_verified |
| I | verification_method |
| J | status |
| K | applied_at |
| L | hr_message_id |
| M | tailored_sent |
| N | docx_filename |
| O | testing |

`testing`: leave empty for production; `Y` for test-lab applies (ignored by production batch).

`status`: skipped_no_email | pending_send | linkedin_lead (legacy) | applied

After LinkedIn export, rows with an `hr_email` use `pending_send`. Batch sets `applied`, fills `hr_message_id`, `tailored_sent` (`Y`), and `docx_filename` when tailored DOCX mail is sent. See [RESUME-TAILORING.md](RESUME-TAILORING.md).

## TESTING (test lab only — not paid seekers)

| A | test_id |
| B | name |
| C | email |
| D | resume_url |
| E | target_role |
| F | domain |
| G | location |
| H | experience_years |
| I | max_applies |
| J | status |
| K | created_at |
| L | last_run_at |
| M | notes |

See [TEST-LAB.md](TEST-LAB.md).

## COMPANY_VERIFIED

| A | company_name |
| B | hr_email |
| C | verified_on |
| D | source |
