#!/usr/bin/env python3
"""Build STEPS docx from STEPS-TO-FOLLOW.md sections (stdlib)."""

import html
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MD = ROOT / "STEPS-TO-FOLLOW.md"
OUT = ROOT.parent / "AI-Job-Consultancy-Steps-To-Follow.docx"
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


def li(t: str) -> str:
    return f'<w:p><w:pPr><w:pStyle w:val="ListBullet"/></w:pPr><w:r><w:t xml:space="preserve">{esc(t)}</w:t></w:r></w:p>'


def md_to_body(text: str) -> str:
    parts = []
    in_code = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            parts.append(p(line, bold=False))
            continue
        if line.startswith("# "):
            parts.append(h(1, line[2:].strip()))
        elif line.startswith("## "):
            parts.append(h(2, line[3:].strip()))
        elif line.startswith("### "):
            parts.append(h(2, line[4:].strip()))
        elif line.startswith("|") and "---" not in line:
            cells = [c.strip() for c in line.split("|")[1:-1]]
            parts.append(p(" | ".join(cells)))
        elif line.startswith("- [ ]"):
            parts.append(li("[ ] " + line[6:].strip()))
        elif line.startswith("- "):
            parts.append(li(line[2:].strip()))
        elif line.strip().startswith(">"):
            parts.append(p(line.strip().lstrip(">").strip(), bold=True))
        elif line.strip():
            parts.append(p(line.strip()))
    return "".join(parts)


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
<w:style w:type="paragraph" w:styleId="Heading1"><w:rPr><w:b/><w:sz w:val="32"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:rPr><w:b/><w:sz w:val="26"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="ListBullet"><w:name w:val="List Bullet"/></w:style>
</w:styles>"""
    core = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>Steps To Follow</dc:title></cp:coreProperties>"""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", doc)
        z.writestr("word/_rels/document.xml.rels", dr)
        z.writestr("word/styles.xml", styles)
        z.writestr("docProps/core.xml", core)


if __name__ == "__main__":
    body = md_to_body(MD.read_text(encoding="utf-8"))
    write_docx(body, OUT)
    print(f"Created {OUT}")
