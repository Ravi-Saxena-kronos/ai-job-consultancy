"""LinkedIn Jobs search via Playwright (local, headed browser)."""

from __future__ import annotations

import random
import time
import urllib.parse
from typing import Callable, Optional

from .linkedin_export import JobListing


def _search_url(keywords: str, location: str) -> str:
    params = {"keywords": keywords}
    if location.strip():
        params["location"] = location.strip()
    q = urllib.parse.urlencode(params)
    return f"https://www.linkedin.com/jobs/search/?{q}"


def _extract_cards_js() -> str:
    return """
    () => {
      const out = [];
      const cards = document.querySelectorAll(
        'li.jobs-search-results__list-item, div.job-search-card, div.base-card[data-entity-urn]'
      );
      for (const card of cards) {
        const link = card.querySelector(
          'a.base-card__full-link, a.job-card-list__title, a[href*="/jobs/view/"]'
        );
        if (!link) continue;
        const href = link.href || '';
        if (!href.includes('/jobs/view/')) continue;
        const titleEl = card.querySelector(
          '.base-search-card__title, .job-card-list__title, h3, strong'
        );
        const companyEl = card.querySelector(
          '.base-search-card__subtitle, .job-card-container__company-name, h4'
        );
        const locEl = card.querySelector(
          '.job-search-card__location, .job-card-container__metadata-item'
        );
        const timeEl = card.querySelector('time');
        let jobId = card.getAttribute('data-entity-urn') || '';
        const m = jobId.match(/:(\\d+)$/);
        jobId = m ? m[1] : '';
        out.push({
          title: (titleEl && titleEl.innerText.trim()) || link.innerText.trim(),
          company: companyEl ? companyEl.innerText.trim() : '',
          location: locEl ? locEl.innerText.trim() : '',
          job_url: href.split('?')[0],
          linkedin_job_id: jobId,
          listed_at: timeEl ? (timeEl.innerText.trim() || timeEl.getAttribute('datetime') || '') : '',
        });
      }
      return out;
    }
    """


def scrape_linkedin_jobs(
    role: str,
    location: str,
    *,
    max_jobs: int = 25,
    user_data_dir: str,
    headless: bool = False,
    fetch_descriptions: bool = False,
    on_wait_login: Optional[Callable[[], None]] = None,
    scroll_pause: float = 1.2,
) -> list[JobListing]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as err:
        raise RuntimeError(
            "Playwright not installed. Run: pip install -r requirements-linkedin-export.txt "
            "&& playwright install chromium"
        ) from err

    url = _search_url(role, location)
    listings: list[JobListing] = []
    seen_urls: set[str] = set()

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=headless,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=120_000)
        if on_wait_login:
            on_wait_login()
        else:
            input(
                "Log in to LinkedIn in the browser if needed, then press Enter when job results are visible… "
            )

        page.goto(url, wait_until="domcontentloaded", timeout=120_000)
        stagnant = 0
        while len(listings) < max_jobs and stagnant < 5:
            batch = page.evaluate(_extract_cards_js())
            added = 0
            for raw in batch:
                job_url = (raw.get("job_url") or "").split("?")[0]
                if not job_url or job_url in seen_urls:
                    continue
                seen_urls.add(job_url)
                listings.append(
                    JobListing(
                        title=(raw.get("title") or "").strip(),
                        company=(raw.get("company") or "").strip(),
                        location=(raw.get("location") or "").strip(),
                        job_url=job_url,
                        linkedin_job_id=str(raw.get("linkedin_job_id") or ""),
                        listed_at=str(raw.get("listed_at") or ""),
                    )
                )
                added += 1
                if len(listings) >= max_jobs:
                    break
            if added == 0:
                stagnant += 1
            else:
                stagnant = 0
            page.mouse.wheel(0, 2400)
            time.sleep(scroll_pause + random.uniform(0.2, 0.8))

        if fetch_descriptions and listings:
            for job in listings[:max_jobs]:
                if not job.job_url:
                    continue
                try:
                    page.goto(job.job_url, wait_until="domcontentloaded", timeout=90_000)
                    time.sleep(random.uniform(1.5, 3.0))
                    desc = page.evaluate(
                        """() => {
                          const el = document.querySelector(
                            '.jobs-description__content, .jobs-box__html-content, #job-details'
                          );
                          return el ? el.innerText : '';
                        }"""
                    )
                    job.description = (desc or "")[:15000]
                except Exception:
                    pass

        context.close()

    return listings[:max_jobs]
