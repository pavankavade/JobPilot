"""
Naukri.com Job Scraper & Extractor.
Uses active logged-in Chrome session via Playwright CDP.
"""

import time
import urllib.parse
from typing import List, Dict, Any
from playwright.sync_api import Page
from job_matcher import calculate_match_score

def search_naukri(page: Page, keyword: str, location: str = "Pune", experience: str = "5", max_pages: int = 2) -> List[Dict[str, Any]]:
    """
    Searches Naukri for given keywords and extracts job postings using your active session.
    """
    print(f"\n[Naukri] Searching for '{keyword}' in '{location}' (Exp: {experience} yrs)...")
    
    # Format search query URL
    # naukri URL format: https://www.naukri.com/jobs-in-india?k=keyword&l=location&experience=5
    query_params = {
        "k": keyword,
        "l": location,
        "experience": experience
    }
    encoded_url = f"https://www.naukri.com/jobs-in-india?{urllib.parse.urlencode(query_params)}"
    
    try:
        page.goto(encoded_url, timeout=45000, wait_until="domcontentloaded")
    except Exception as e:
        print(f"[Naukri] Navigation notice: {e}")

    # Allow dynamic client side rendering
    time.sleep(4)

    all_jobs = []

    for current_page in range(1, max_pages + 1):
        print(f"[Naukri] Scanning page {current_page}...")

        # Scroll down smoothly to trigger lazy-loaded cards
        for _ in range(4):
            page.mouse.wheel(0, 800)
            time.sleep(1.0)

        # Extract job cards using JavaScript for speed and reliability
        raw_jobs = page.evaluate('''() => {
            const results = [];
            // Select all possible card containers
            const cards = document.querySelectorAll('.srp-jobtuple-wrapper, article.jobTuple, div.cust-job-tuple, .tuple');
            
            cards.forEach(card => {
                const titleEl = card.querySelector('.title, a.title, [class*="title"]');
                const compEl = card.querySelector('.comp-name, a.comp-name, [class*="comp-name"], [class*="company"]');
                const expEl = card.querySelector('.exp-wrap, span.expwdth, [class*="exp"]');
                const locEl = card.querySelector('.loc-wrap, span.locWdth, [class*="loc"]');
                const salEl = card.querySelector('.sal-wrap, span.sal, [class*="sal"]');
                const descEl = card.querySelector('.job-desc, [class*="job-desc"], [class*="jobDescription"]');
                
                const tagEls = card.querySelectorAll('ul.tags-gt li, .dot-gt li, [class*="tag"] li, .tag-li');
                const tags = Array.from(tagEls).map(t => t.innerText.trim()).filter(Boolean);

                const title = titleEl ? titleEl.innerText.trim() : '';
                const link = titleEl && titleEl.href ? titleEl.href : (card.querySelector('a') ? card.querySelector('a').href : '');
                const company = compEl ? compEl.innerText.trim() : '';
                const experience = expEl ? expEl.innerText.trim() : '';
                const location = locEl ? locEl.innerText.trim() : '';
                const salary = salEl ? salEl.innerText.trim() : 'Not disclosed';
                const description = descEl ? descEl.innerText.trim() : '';

                if (title) {
                    results.push({
                        portal: 'Naukri',
                        title,
                        company,
                        experience,
                        location,
                        salary,
                        description,
                        tags,
                        link
                    });
                }
            });
            return results;
        }''')

        print(f"[Naukri] Extracted {len(raw_jobs)} job postings on page {current_page}.")

        for job in raw_jobs:
            score_data = calculate_match_score(job)
            job.update(score_data)
            all_jobs.append(job)

        # Check if there is a next page
        if current_page < max_pages:
            try:
                next_btn = page.query_selector('a:has-text("Next"), a.fright, .next')
                if next_btn and next_btn.is_visible():
                    next_btn.click()
                    time.sleep(4)
                else:
                    break
            except Exception:
                break

    print(f"[Naukri] Completed search for '{keyword}'. Total jobs: {len(all_jobs)}")
    return all_jobs
