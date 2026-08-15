"""
LinkedIn Jobs Scraper & Extractor.
Uses active logged-in Chrome session via Playwright CDP.
"""

import time
import urllib.parse
from typing import List, Dict, Any
from playwright.sync_api import Page
from job_matcher import calculate_match_score

def search_linkedin(page: Page, keyword: str, location: str = "Pune", max_pages: int = 1) -> List[Dict[str, Any]]:
    """
    Searches LinkedIn for jobs using your active logged-in profile.
    """
    print(f"\n[LinkedIn] Searching for '{keyword}' in '{location}'...")

    # Build LinkedIn jobs search URL
    # f_TPR=r604800 filters for jobs posted in the past week
    query_params = {
        "keywords": keyword,
        "location": location,
        "f_TPR": "r604800"
    }
    encoded_url = f"https://www.linkedin.com/jobs/search/?{urllib.parse.urlencode(query_params)}"

    try:
        page.goto(encoded_url, timeout=45000, wait_until="domcontentloaded")
    except Exception as e:
        print(f"[LinkedIn] Navigation notice: {e}")

    # Allow dynamic feed rendering
    time.sleep(5)

    all_jobs = []

    # Scroll the job results list panel
    for scroll_idx in range(6):
        # Try scrolling the dedicated results list container or full window
        page.evaluate('''() => {
            const listContainer = document.querySelector('.jobs-search-results-list, .scaffold-layout__list');
            if (listContainer) {
                listContainer.scrollTop += 600;
            } else {
                window.scrollBy(0, 600);
            }
        }''')
        time.sleep(1.5)

    # Extract job card details
    raw_jobs = page.evaluate('''() => {
        const results = [];
        const cardSelectors = [
            'li.jobs-search-results__list-item',
            'div.job-card-container',
            'div.base-card',
            '.scaffold-layout__list-item'
        ];

        let cards = [];
        for (const selector of cardSelectors) {
            const found = document.querySelectorAll(selector);
            if (found && found.length > 0) {
                cards = Array.from(found);
                break;
            }
        }

        cards.forEach(card => {
            const titleEl = card.querySelector('a.job-card-list__title, a.job-card-container__link, strong, h3');
            const compEl = card.querySelector('.artdeco-entity-lockup__subtitle, .job-card-container__primary-description, [class*="company"]');
            const locEl = card.querySelector('.job-card-container__metadata-item, [class*="location"]');
            const easyApplyEl = card.querySelector('[aria-label*="Easy Apply"], .job-card-container__apply-method');

            const title = titleEl ? titleEl.innerText.trim() : '';
            let link = titleEl && titleEl.href ? titleEl.href : '';
            if (!link) {
                const anyLink = card.querySelector('a');
                if (anyLink) link = anyLink.href;
            }

            const company = compEl ? compEl.innerText.trim() : '';
            const location = locEl ? locEl.innerText.trim() : '';
            const isEasyApply = !!easyApplyEl;

            if (title && !title.includes('\\n')) {
                results.push({
                    portal: 'LinkedIn',
                    title,
                    company,
                    location,
                    salary: 'See posting',
                    description: '',
                    tags: isEasyApply ? ['Easy Apply'] : [],
                    link
                });
            }
        });

        return results;
    }''')

    print(f"[LinkedIn] Extracted {len(raw_jobs)} job postings.")

    for job in raw_jobs:
        score_data = calculate_match_score(job)
        job.update(score_data)
        all_jobs.append(job)

    print(f"[LinkedIn] Completed search for '{keyword}'. Total jobs: {len(all_jobs)}")
    return all_jobs
