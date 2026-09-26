"""LinkedIn content search — human-like scroll, expand posts, grep emails + company."""

from __future__ import annotations

import hashlib
import random
import re
import time
import urllib.parse
from pathlib import Path
from typing import Callable, Optional

from . import hr_verify
from .linkedin_export import JobListing

SEE_MORE_SELECTORS = (
    "button:has-text('…more')",
    "button:has-text('...more')",
    "button:has-text('see more')",
    "button:has-text('See more')",
    "button.feed-shared-inline-show-more-text",
    "span.feed-shared-inline-show-more-text",
    ".feed-shared-text-view button",
    'button[aria-label*="see more" i]',
)

_EXTRACT_POSTS_JS = """
() => {
  const main = document.querySelector('main');
  if (!main) return [];

  const emailRe = /[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,}/i;
  const hireRe = /\\b(hiring|we'?re hiring|join (?:us|our team)|vacancy|opening|immediate joiner)\\b/i;
  const seen = new Set();
  const posts = [];

  function add(text) {
    const t = (text || '').trim();
    if (t.length < 80 || t.length > 20000) return;
    const hasEmail = emailRe.test(t);
    const hasHire = hireRe.test(t);
    if (!hasEmail && !hasHire) return;
    const key = t.slice(0, 320);
    if (seen.has(key)) return;
    seen.add(key);
    const lines = t.split('\\n').map((l) => l.trim()).filter(Boolean);
    let author = '';
    for (const line of lines.slice(0, 6)) {
      if (line.length > 2 && line.length < 80 && !/^\\d/.test(line) && !line.includes('followers')) {
        author = line;
        break;
      }
    }
    posts.push({ text: t, author });
  }

  // 1) Known containers (when LinkedIn uses them)
  const containerSels = [
    'div.feed-shared-update-v2',
    'div[class*="feed-shared-update"]',
    'li.reusable-search__result-container',
    'div[data-chameleon-result-urn]',
    'div[data-urn*="ugcPost"]',
    'div[data-urn*="activity"]',
    'article',
    '[data-view-name*="result"]',
    '[data-view-name*="update"]',
    '[data-view-name*="feed"]',
  ];
  for (const sel of containerSels) {
    main.querySelectorAll(sel).forEach((el) => add(el.innerText));
  }

  // 2) Smallest block around each email (works when class names change)
  const walker = document.createTreeWalker(main, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const node = walker.currentNode;
    const chunk = (node.textContent || '').trim();
    if (!emailRe.test(chunk)) continue;
    let el = node.parentElement;
    for (let depth = 0; depth < 12 && el && el !== main; depth++) {
      const block = (el.innerText || '').trim();
      if (block.length >= 120 && block.length <= 16000) {
        add(block);
        break;
      }
      el = el.parentElement;
    }
  }

  // 3) Hiring headlines without email yet (expand "more" on next pass)
  main.querySelectorAll('div, li, article').forEach((el) => {
    const t = (el.innerText || '').trim();
    if (t.length < 100 || t.length > 4000) return;
    if (!hireRe.test(t)) return;
    if (el.querySelector('div, li, article') && (el.innerText || '').length > 3500) return;
    add(t);
  });

  return posts;
}
"""


def content_search_url(keywords: str) -> str:
    q = urllib.parse.quote(keywords.strip())
    return (
        "https://www.linkedin.com/search/results/content/"
        f"?keywords={q}&origin=SWITCH_SEARCH_VERTICAL"
    )


_JUNK_COMPANY_RE = re.compile(
    r"^(feed post|key skills|apply today|promoted|requirements?)$",
    re.I,
)


def _unique_job_url(email: str, post_key: str) -> str:
    raw = f"{hr_verify.normalize_email(email)}|{post_key[:240]}"
    digest = hashlib.sha256(raw.encode()).hexdigest()[:24]
    return f"https://www.linkedin.com/content-export/{digest}"


def _title_from_post(text: str, role: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if re.search(r"hiring|devops|engineer|opening|vacancy", line, re.I) and len(line) < 120:
            return line
    return f"{role} — content post"


def _company_from_post(text: str, author: str = "") -> str:
    def ok(name: str) -> bool:
        name = (name or "").strip()
        return len(name) > 2 and not _JUNK_COMPANY_RE.match(name)

    patterns = (
        r"[Hh]iring\s*\|\s*[^|]+\|\s*([^\n|]+)",
        r"Founder of\s+['\"]([^'\"]+)['\"]",
        r"Founder of\s+([^\n'\"]+)",
        r"join (?:our (?:growing )?team at|us at)\s+([^\n.!]+)",
        r"team at\s+([^\n.!]+)",
        r"([A-Z][A-Za-z0-9 &.'-]{2,55})\s+is [Hh]iring",
        r"[Hh]iring (?:for|at)\s+([^\n:–-]+)",
        r"🚀\s*([^–\n:]+(?:Engineer|Developer|DevOps)[^\n]*)",
    )
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            name = m.group(1).strip().strip(":")
            if ok(name):
                return name[:100]

    for line in text.splitlines():
        line = line.strip()
        if "View job" in line or line.startswith("Promoted"):
            continue
        if re.match(r"^[A-Z][A-Za-z0-9 .&'-]{2,50}$", line) and "Engineer" not in line:
            if "hiring" not in line.lower() and ok(line):
                return line[:100]

    emails = hr_verify.extract_post_emails(text, allow_free_mail=True)
    for email in emails:
        domain = email.split("@")[-1].lower()
        if hr_verify.is_free_mail(email):
            continue
        base = domain.split(".")[0]
        if len(base) >= 3:
            return base.replace("-", " ").title()

    author_line = (author or "").strip()
    if author_line and ok(author_line):
        return author_line[:80]
    first = (text.splitlines()[0] if text else "").strip()
    return first[:80] if first else "LinkedIn content"


def _expand_see_more_on_page(page) -> int:
    clicked = 0
    for sel in SEE_MORE_SELECTORS:
        try:
            loc = page.locator(sel)
            n = loc.count()
            for i in range(min(n, 25)):
                btn = loc.nth(i)
                try:
                    if btn.is_visible():
                        btn.click(timeout=1500)
                        clicked += 1
                        time.sleep(0.2 + random.uniform(0, 0.15))
                except Exception:
                    continue
        except Exception:
            continue
    return clicked


def _human_scroll_step(page) -> None:
    main = page.locator("main").first
    try:
        if main.count():
            main.hover(timeout=2000)
    except Exception:
        pass
    try:
        page.keyboard.press("PageDown")
    except Exception:
        pass
    delta = random.randint(500, 1100)
    page.mouse.wheel(0, delta)
    for sel in (
        ".scaffold-finite-scroll__content",
        ".search-results-container",
        "div.scaffold-layout__list",
    ):
        el = page.query_selector(sel)
        if el:
            try:
                el.evaluate("el => { el.scrollTop += el.clientHeight * 0.85; }")
            except Exception:
                pass
            break
    time.sleep(random.uniform(0.9, 1.8))


def _collect_posts(page) -> list[dict]:
    raw = page.evaluate(_EXTRACT_POSTS_JS)
    return raw if isinstance(raw, list) else []


def scrape_content_emails(
    role: str,
    *,
    max_posts: int = 30,
    max_leads: int = 25,
    user_data_dir: str,
    on_wait_login: Optional[Callable[[], None]] = None,
    debug: bool = False,
    scroll_rounds: int = 40,
) -> list[JobListing]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as err:
        raise RuntimeError("pip install playwright && playwright install chromium") from err

    url = content_search_url(role)
    listings: list[JobListing] = []
    seen_emails: set[str] = set()
    seen_post_keys: set[str] = set()

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            viewport={"width": 1400, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else context.new_page()
        print(f"Opening content search: {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=120_000)
        if on_wait_login:
            on_wait_login()
        else:
            input(
                "Log in if needed. When CONTENT posts are visible, press Enter (page will NOT reload)… "
            )

        if "search/results/content" not in (page.url or ""):
            page.goto(url, wait_until="domcontentloaded", timeout=120_000)
            time.sleep(2.0)

        print(
            f"Human pass: scroll feed until {max_leads} unique email lead(s) "
            f"(--max-jobs) are collected…"
        )
        posts_scanned = 0
        stagnant = 0
        max_rounds = max(scroll_rounds, max_leads * 12)

        for round_i in range(1, max_rounds + 1):
            if len(listings) >= max_leads:
                print(f"  collected {max_leads} email lead(s) — stopping scroll")
                break

            expanded = _expand_see_more_on_page(page)
            batch = _collect_posts(page)
            new_posts = 0

            for item in batch:
                if len(listings) >= max_leads:
                    break
                text = (item.get("text") or "").strip()
                author = (item.get("author") or "").strip()
                key = text[:320]
                if not key or key in seen_post_keys:
                    continue
                seen_post_keys.add(key)
                posts_scanned += 1
                new_posts += 1

                emails = hr_verify.extract_post_emails(text, allow_free_mail=True)
                company = _company_from_post(text, author)
                title = _title_from_post(text, role)

                print(
                    f"  [{round_i}] post #{posts_scanned}: "
                    f"{len(emails)} email(s), company≈{company[:50]!r}"
                )

                if not emails:
                    continue

                for email in emails:
                    norm = hr_verify.normalize_email(email)
                    if norm in seen_emails:
                        continue
                    seen_emails.add(norm)
                    listings.append(
                        JobListing(
                            title=title,
                            company=company,
                            location="",
                            job_url=_unique_job_url(norm, key),
                            description=f"{norm}\n{text}"[:15000],
                        )
                    )
                    if len(listings) >= max_leads:
                        break

            if new_posts == 0 and expanded == 0:
                stagnant += 1
            else:
                stagnant = 0

            if round_i % 5 == 0 or debug:
                main_len = page.evaluate(
                    "() => (document.querySelector('main') || {}).innerText?.length || 0"
                )
                print(
                    f"  scroll round {round_i}/{max_rounds}: "
                    f"posts_seen={posts_scanned}, emails={len(seen_emails)}, "
                    f"main_chars={main_len}, …more_clicks={expanded}"
                )

            if stagnant >= 8 and posts_scanned > 0:
                print("  reached end of feed (no new posts after scrolling)")
                break

            _human_scroll_step(page)

        if debug or not listings:
            shot = Path(user_data_dir).parent / "linkedin-content-debug.png"
            try:
                page.screenshot(path=str(shot), full_page=False)
                print(f"debug: screenshot={shot}")
            except Exception:
                pass

        print(
            f"Summary: posts_read={posts_scanned}, "
            f"unique_emails={len(seen_emails)}, sheet_rows={len(listings)}"
        )
        context.close()

    return listings
