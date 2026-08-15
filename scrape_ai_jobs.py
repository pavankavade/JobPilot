"""
Dedicated AI Developer & AI Architect Job Harvester.
Scrapes targeted Generative AI, AI Solutions Architect, and Azure OpenAI jobs via active Chrome CDP.
"""

import time
from playwright.sync_api import sync_playwright
from config import CDP_URL
from scrapers.naukri_scraper import search_naukri
from scrapers.linkedin_scraper import search_linkedin
from database import upsert_job, get_stats

AI_SEARCH_QUERIES = [
    {"keyword": "Generative AI Developer", "location": "Pune", "exp": "5"},
    {"keyword": "AI Engineer Azure OpenAI", "location": "Pune", "exp": "5"},
    {"keyword": "AI Solutions Architect", "location": "Pune", "exp": "5"},
    {"keyword": "AI Architect", "location": "Remote", "exp": "5"},
    {"keyword": "Generative AI Engineer", "location": "Remote", "exp": "5"},
    {"keyword": "AI Tech Lead", "location": "Pune", "exp": "5"},
    {"keyword": "GenAI Full Stack Developer", "location": "Pune", "exp": "5"}
]

def harvest_ai_jobs():
    print("="*60)
    print(" Harvesting Dedicated AI & Architecture Roles...")
    print("="*60)

    total_added = 0

    with sync_playwright() as p:
        print("[*] Connecting to Chrome session on port 9222...")
        browser = p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.new_page()

        try:
            for q in AI_SEARCH_QUERIES:
                kw = q["keyword"]
                loc = q["location"]
                exp = q["exp"]

                print(f"\n[AI Scanner] Querying '{kw}' ({loc})...")
                # Search Naukri
                naukri_results = search_naukri(page, keyword=kw, location=loc, experience=exp, max_pages=1)
                for job in naukri_results:
                    job_id = upsert_job(job)
                    if job_id:
                        total_added += 1

                time.sleep(1.5)

                # Search LinkedIn
                linkedin_results = search_linkedin(page, keyword=kw, location=loc, max_pages=1)
                for job in linkedin_results:
                    job_id = upsert_job(job)
                    if job_id:
                        total_added += 1

                time.sleep(1.5)

        finally:
            try:
                page.close()
            except Exception:
                pass

    print("\n" + "="*60)
    print(f" [SUCCESS] Harvested & scored new AI roles! Total in DB: {get_stats()['total']}")
    print("="*60)

if __name__ == "__main__":
    harvest_ai_jobs()
