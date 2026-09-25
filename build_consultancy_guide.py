#!/usr/bin/env python3
"""Generate AI Job Consultancy full working model DOCX (stdlib only)."""

import html
import zipfile
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "AI-Job-Consultancy-Full-Working-Model.docx"
WNS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def esc(t: str) -> str:
    return html.escape(t, quote=False)


def p(t: str, bold=False) -> str:
    rpr = "<w:rPr><w:b/></w:rPr>" if bold else ""
    return f'<w:p><w:r>{rpr}<w:t xml:space="preserve">{esc(t)}</w:t></w:r></w:p>'


def h(level: int, t: str) -> str:
    return (
        f'<w:p><w:pPr><w:pStyle w:val="Heading{level}"/></w:pPr>'
        f'<w:r><w:t>{esc(t)}</w:t></w:r></w:p>'
    )


def li(t: str, num=False) -> str:
    st = "ListNumber" if num else "ListBullet"
    return f'<w:p><w:pPr><w:pStyle w:val="{st}"/></w:pPr><w:r><w:t xml:space="preserve">{esc(t)}</w:t></w:r></w:p>'


def table(headers, rows):
    parts = ["<w:tbl><w:tblPr><w:tblW w:w=\"5000\" w:type=\"pct\"/><w:tblBorders>"
             "<w:top w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"auto\"/>"
             "<w:left w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"auto\"/>"
             "<w:bottom w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"auto\"/>"
             "<w:right w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"auto\"/>"
             "<w:insideH w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"auto\"/>"
             "<w:insideV w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"auto\"/>"
             "</w:tblBorders></w:tblPr><w:tr>"]
    for c in headers:
        parts.append(f"<w:tc><w:p><w:r><w:rPr><w:b/></w:rPr><w:t>{esc(c)}</w:t></w:r></w:p></w:tc>")
    parts.append("</w:tr>")
    for row in rows:
        parts.append("<w:tr>")
        for c in row:
            parts.append(f'<w:tc><w:p><w:r><w:t xml:space="preserve">{esc(c)}</w:t></w:r></w:p></w:tc>')
        parts.append("</w:tr>")
    parts.append("</w:tbl>")
    return "".join(parts)


def build_body() -> str:
    x = []
    x.append(p("AI Job Consultancy + AI Resume Post Backend", bold=True))
    x.append(p("Email-only job seeker service | Full working model | 25 September 2026"))
    x.append(p("Planning document — not legal advice. LinkedIn auto-apply is not part of this model.", bold=True))

    x.append(h(1, "1. Your two apps (one business)"))
    x.append(table(
        ["App", "Who uses it", "Purpose"],
        [
            ("AI Consultancy (public website)", "Job seekers", "Pay Rs 99 registration, upload resume, buy 5/10/15/20/30 company packages — no phone, email only"),
            ("AI Resume Post (private backend)", "You + automation", "Match resume to roles, queue applications, email companies or seeker, log every step, notify seeker by email"),
        ],
    ))

    x.append(h(1, "2. What is realistic (read before building)"))
    for t in [
        "LinkedIn does not allow bots to search and auto-apply. Doing so risks bans and legal exposure.",
        "You cannot upload a file into most company HR systems without their careers portal or API.",
        "Mass cold email to random HR addresses is spam and hurts your domain.",
        "Working model: AI finds matching public jobs + your curated company list; sends application only to official careers emails OR sends seeker an apply link with ready resume and cover letter.",
    ]:
        x.append(li(t))

    x.append(h(1, "3. Pricing model (you can change later)"))
    x.append(table(
        ["Product code", "Price (example)", "Includes"],
        [
            ("REG-99", "Rs 99", "Account + resume storage + AI review summary email"),
            ("POST-5", "+ Rs 399", "5 outreach actions logged and emailed to seeker"),
            ("POST-10", "+ Rs 699", "10 actions"),
            ("POST-15", "+ Rs 999", "15 actions"),
            ("POST-20", "+ Rs 1299", "20 actions"),
            ("POST-30", "+ Rs 1799", "30 actions"),
        ],
    ))
    x.append(p("One action = one company + one role attempt, recorded with timestamp and method (email apply or link sent to seeker)."))

    x.append(h(1, "4. End-to-end flow (automated where safe)"))
    numbered = [
        "Seeker opens website, enters email only (magic link login, no phone).",
        "Pays Rs 99 via Razorpay; receipt email sent.",
        "Uploads resume PDF; system emails: Received + expected timeline.",
        "Optional: buys POST-5 / 10 / 15 pack; payment recorded.",
        "Backend parses resume (skills, years, location, role target).",
        "Matcher scores jobs from your company database + public job feeds.",
        "For each slot in package: generate cover letter; attach resume; send via your domain OR email seeker official apply URL.",
        "Email seeker: Applied to [Company] for [Role] on [date], reference APS-12345.",
        "When package exhausted, email: Upgrade to POST-10 if you want more.",
    ]
    for i, t in enumerate(numbered, 1):
        x.append(li(f"{i}. {t}", num=True))

    x.append(h(1, "5. Requirements from YOU"))
    x.append(h(2, "5.1 Business"))
    for t in [
        "Company name and brand (e.g. AI Job Consultancy).",
        "Proprietorship or Pvt Ltd; GST when turnover requires.",
        "Bank account for Razorpay settlements.",
        "Privacy Policy, Terms of Service, Refund policy on website.",
        "Written consent on site: seeker authorizes you to send resume to employers on their behalf.",
        "DPDP Act: data retention period (e.g. 12 months) and deletion request process.",
    ]:
        x.append(li(t))

    x.append(h(2, "5.2 Technical assets"))
    x.append(table(
        ["Item", "Why"],
        [
            ("Domain + business email", "apply@yourdomain.com, noreply@ for automation"),
            ("SPF, DKIM, DMARC", "Without these, status emails go to spam"),
            ("Razorpay business account", "Rs 99 + packages"),
            ("Hosting (Vercel / Render)", "Public consultancy site"),
            ("Database (Supabase Postgres free tier)", "Seekers, resumes, applications"),
            ("Private file storage", "Resumes encrypted; never public URLs"),
            ("Email API (Resend / Amazon SES)", "All seeker and apply emails"),
            ("LLM API key", "Parse resume + cover letter (OpenAI or similar)"),
            ("Curated company CSV (50–200 rows)", "company, role family, careers email or apply URL, experience band"),
        ],
    ))

    x.append(h(2, "5.3 Operational"))
    for t in [
        "Pick 2–3 niches first (e.g. Java 2–5 yrs Delhi NCR, inside sales, accountant).",
        "Human review first 50 seekers before full automation.",
        "Support inbox: support@yourdomain.com — reply within 24h.",
    ]:
        x.append(li(t))

    x.append(h(1, "6. Technology architecture"))
    x.append(p("Public: static/Next site → API → DB + storage. Private admin: queue, approve, rerun matcher. Worker cron every 15 min processes pending applications."))
    x.append(table(
        ["Component", "Tool", "Cost start"],
        [
            ("Frontend", "HTML on Vercel or Next.js", "Free tier"),
            ("API", "Python FastAPI or Node", "Free/low"),
            ("Payments", "Razorpay", "Per transaction fee"),
            ("Email", "Resend / SES", "Low per 1000 emails"),
            ("AI", "OpenAI API", "Pay per resume"),
            ("Queue", "DB table + cron or Upstash Redis", "Free tier"),
        ],
    ))

    x.append(h(1, "7. AI Resume Post — matching logic"))
    for t in [
        "Extract: name, email, phone (stored but not shown in UI if email-only product), skills, employers, years, education, preferred city.",
        "Job record: title, min/max experience, skills required, location, apply_email or apply_url.",
        "Score = skill overlap + experience in range + location match.",
        "Take top N jobs where N = package remaining count.",
        "Never apply twice same company within 90 days for same seeker.",
    ]:
        x.append(li(t))

    x.append(h(1, "8. Email templates you need"))
    for t in [
        "Magic link login",
        "Payment receipt (Rs 99 and packs)",
        "Resume received",
        "Application sent to Company X",
        "Apply yourself — link + attachments (when no careers email)",
        "Package 80% used warning",
        "Package complete + upsell",
    ]:
        x.append(li(t))
    x.append(p("Samples in repo: ai-job-consultancy/docs/email-templates/"))

    x.append(h(1, "9. Minimum investment"))
    x.append(table(
        ["Item", "Approx Rs"],
        [
            ("Domain 1 year", "500–800"),
            ("Razorpay", "0 setup"),
            ("Email + hosting first month", "0–2000"),
            ("LLM testing", "500–2000"),
            ("Legal templates (optional lawyer)", "5000+"),
            ("Total MVP", "3000–15000 excluding your time"),
        ],
    ))

    x.append(h(1, "10. 30-day launch plan"))
    x.append(table(
        ["Week", "Tasks"],
        [
            ("1", "Domain, email DNS, legal pages, Razorpay, company CSV 50 rows"),
            ("2", "Upload + pay Rs 99 + magic link + receipt email"),
            ("3", "Admin dashboard + POST packages + resume parser"),
            ("4", "Worker: match + send + seeker notification emails; soft launch + publicity"),
        ],
    ))

    x.append(h(1, "11. Publicity (free / open platforms) — after MVP works"))
    x.append(table(
        ["Platform", "Action"],
        [
            ("GitHub", "Open-source landing page or resume checklist; link to paid service"),
            ("Product Hunt", "Launch with demo video"),
            ("Dev.to / Hashnode", "Technical blog: email-only job pipeline"),
            ("Reddit", "r/developersIndia, r/india — follow rules"),
            ("Hacker News", "Show HN — honest scope"),
            ("Google Search Console", "Index your site"),
            ("AlternativeTo, SaaSHub", "Free listings"),
            ("Your LinkedIn", "Manual posts — do not automate applies on LinkedIn"),
        ],
    ))

    x.append(h(1, "12. What we created in your project folder"))
    for t in [
        "ai-job-consultancy/README.md and ARCHITECTURE.md",
        "ai-job-consultancy/web/index.html — landing preview",
        "ai-job-consultancy/docs/email-templates/ — starter copy",
        "Regenerate this file: python3 ai-job-consultancy/build_consultancy_guide.py",
    ]:
        x.append(li(t))

    x.append(p("Next build step: connect Razorpay + Supabase + resume upload API (Phase 1 code).", bold=True))
    return "".join(x)


def write_docx(body: str, path: Path) -> None:
    doc = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{WNS}"><w:body>{body}
<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>
<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr>
</w:body></w:document>"""
    ct = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.styles+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
</Types>"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
</Relationships>"""
    dr = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""
    styles = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{WNS}">
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:rPr><w:b/><w:sz w:val="32"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:rPr><w:b/><w:sz w:val="26"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="ListBullet"><w:name w:val="List Bullet"/></w:style>
<w:style w:type="paragraph" w:styleId="ListNumber"><w:name w:val="List Number"/></w:style>
</w:styles>"""
    core = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>AI Job Consultancy Model</dc:title></cp:coreProperties>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", doc)
        z.writestr("word/_rels/document.xml.rels", dr)
        z.writestr("word/styles.xml", styles)
        z.writestr("docProps/core.xml", core)


if __name__ == "__main__":
    write_docx(build_body(), OUT)
    print(f"Created {OUT}")
