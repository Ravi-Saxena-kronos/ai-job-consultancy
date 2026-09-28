"""LinkedIn Jobs search via Playwright (local, headed browser)."""

from __future__ import annotations

import random
import time
import urllib.parse
from pathlib import Path
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
      const seen = new Set();

      function addFromCard(card, link) {
        const href = (link.href || '').split('?')[0];
        if (!href.includes('/jobs/view/') || seen.has(href)) return;
        seen.add(href);
        const titleEl = card.querySelector(
          '.base-search-card__title, .job-card-list__title, .job-card-container__link, h3, strong'
        );
        const companyEl = card.querySelector(
          '.base-search-card__subtitle, .job-card-container__company-name, .artdeco-entity-lockup__subtitle, h4'
        );
        const locEl = card.querySelector(
          '.job-search-card__location, .job-card-container__metadata-item, .artdeco-entity-lockup__caption'
        );
        const timeEl = card.querySelector('time');
        let jobId = card.getAttribute('data-occludable-job-id')
          || card.getAttribute('data-job-id') || '';
        const urn = card.getAttribute('data-entity-urn') || '';
        const m = urn.match(/:(\\d+)$/);
        if (m) jobId = m[1];
        out.push({
          title: (titleEl && titleEl.innerText.trim()) || link.innerText.trim(),
          company: companyEl ? companyEl.innerText.trim() : '',
          location: locEl ? locEl.innerText.trim() : '',
          job_url: href,
          linkedin_job_id: jobId,
          listed_at: timeEl ? (timeEl.innerText.trim() || timeEl.getAttribute('datetime') || '') : '',
        });
      }

      const cardSelectors = [
        'li.jobs-search-results__list-item',
        'li.scaffold-layout__list-item',
        'div.job-search-card',
        'div.base-card[data-entity-urn]',
        'div.job-card-container',
      ];
      for (const sel of cardSelectors) {
        for (const card of document.querySelectorAll(sel)) {
          const link = card.querySelector(
            'a.base-card__full-link, a.job-card-list__title, a.job-card-container__link, a[href*="/jobs/view/"]'
          );
          if (link) addFromCard(card, link);
        }
      }

      if (out.length === 0) {
        for (const link of document.querySelectorAll('a[href*="/jobs/view/"]')) {
          const card = link.closest('li, div.job-card-container, div.base-card') || link;
          addFromCard(card, link);
        }
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
    scroll_pause: float = 1.5,
    debug: bool = False,
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
            viewport={"width": 1400, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else context.new_page()
        print(f"Opening: {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=120_000)
        if on_wait_login:
            on_wait_login()
        else:
            input(
                "Log in to LinkedIn in the browser if needed, then press Enter when job results are visible… "
            )

        page.goto(url, wait_until="domcontentloaded", timeout=120_000)
        try:
            page.wait_for_selector('a[href*="/jobs/view/"]', timeout=45_000)
        except Exception:
            print("warn: no job links visible yet — scroll the left job list or fix login")

        list_selectors = (
            ".jobs-search-results-list",
            ".scaffold-layout__list",
            "div.jobs-search-results-list",
        )
        list_el = None
        for sel in list_selectors:
            list_el = page.query_selector(sel)
            if list_el:
                break

        stagnant = 0
        while len(listings) < max_jobs and stagnant < 8:
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
            if list_el:
                list_el.evaluate("el => el.scrollTop = el.scrollHeight")
            else:
                page.mouse.wheel(0, 2000)
            time.sleep(scroll_pause + random.uniform(0.3, 1.0))

        if debug or not listings:
            link_count = page.evaluate(
                '() => document.querySelectorAll(\'a[href*="/jobs/view/"]\').length'
            )
            shot = Path(user_data_dir).parent / "linkedin-debug.png"
            try:
                page.screenshot(path=str(shot), full_page=False)
                print(f"debug: job links on page={link_count}, screenshot={shot}")
            except Exception:
                print(f"debug: job links on page={link_count}, url={page.url}")

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
                            '.jobs-description__content, .jobs-box__html-content, #job-details, .jobs-description-content'
                          );
                          return el ? el.innerText : '';
                        }"""
                    )
                    job.description = (desc or "")[:15000]
                except Exception:
                    pass

        context.close()

    return listings[:max_jobs]
