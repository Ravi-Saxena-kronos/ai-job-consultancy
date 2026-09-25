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

`status`: skipped_no_email | applied

## COMPANY_VERIFIED

| A | company_name |
| B | hr_email |
| C | verified_on |
| D | source |
