"""
Automated Job Search Runner.
Connects to your active Chrome instance via CDP and searches for matched jobs.
"""

import os
import csv
import json
import time
import sys
from datetime import datetime
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright

from config import CDP_URL, SEARCH_QUERIES, CANDIDATE_PROFILE
from scrapers.naukri_scraper import search_naukri
from scrapers.linkedin_scraper import search_linkedin

def test_cdp_connection() -> bool:
    """Checks if Chrome is listening on port 9222."""
    import urllib.request
    try:
        req = urllib.request.Request(f"{CDP_URL}/json/version")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            print(f"[SUCCESS] Connected to Chrome: {data.get('Browser', 'Chrome')}")
            return True
    except Exception:
        return False

def save_results(jobs: List[Dict[str, Any]]):
    """Saves extracted job data into CSV and JSON files."""
    if not jobs:
        print("\n[!] No jobs collected to save.")
        return

    # Deduplicate based on title and company
    unique_jobs = []
    seen = set()
    for j in jobs:
        key = (j.get("portal", ""), j.get("company", "").lower(), j.get("title", "").lower())
        if key not in seen:
            seen.add(key)
            unique_jobs.append(j)

    # Sort descending by match score
    unique_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = f"jobs_{timestamp}.csv"
    latest_csv = "jobs_latest.csv"
    json_file = "jobs_latest.json"

    # Write CSV
    fieldnames = [
        "match_score",
        "portal",
        "title",
        "company",
        "location",
        "salary",
        "matched_primary",
        "matched_secondary",
        "link",
        "tags"
    ]

    for filename in [csv_file, latest_csv]:
        with open(filename, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for job in unique_jobs:
                row = dict(job)
                row["matched_primary"] = ", ".join(job.get("matched_primary", []))
                row["matched_secondary"] = ", ".join(job.get("matched_secondary", []))
                row["tags"] = ", ".join(job.get("tags", []))
                writer.writerow(row)

    # Save to SQLite Database
    import database
    for job in unique_jobs:
        database.upsert_job(job)

    print(f"\n" + "="*70)
    print(f" JOB SEARCH COMPLETED: {len(unique_jobs)} UNIQUE ROLES FOUND")
    print(f"="*70)
    print(f"-> Saved latest results to: {latest_csv}")
    print(f"-> Saved backup to:         {csv_file}")
    print(f"-> Saved JSON to:           {json_file}")
    print(f"="*70)

    # Print Top 10 matches to console
    print("\n--- TOP MATCHED ROLES ---")
    for idx, job in enumerate(unique_jobs[:10], start=1):
        score = job.get('match_score', 0)
        print(f"\n{idx}. [{score}% Match] [{job.get('portal')}] {job.get('title')}")
        print(f"   Company:  {job.get('company')} | Location: {job.get('location')}")
        if job.get('salary') and job.get('salary') != 'Not disclosed':
            print(f"   Salary:   {job.get('salary')}")
        print(f"   Skills:   {', '.join(job.get('matched_primary', []))}")
        print(f"   Link:     {job.get('link')}")

def run_job_search(portal_choice: str = "both"):
    """
    Main orchestration function connecting to Chrome via CDP.
    """
    print("\n========================================================")
    print(f" Automated Job Search for: {CANDIDATE_PROFILE['name']}")
    print(f" Core Stack: {', '.join(CANDIDATE_PROFILE['primary_skills'][:5])}")
    print("========================================================\n")

    if not test_cdp_connection():
        print("\n[ERROR] Could not connect to Chrome on port 9222!")
        print("Please run launch_chrome.bat first to start Chrome in Remote Debugging mode.")
        print("Command: .\\launch_chrome.bat")
        return

    all_found_jobs = []

    with sync_playwright() as p:
        print("[*] Connecting to running Chrome session via CDP...")
        try:
            browser = p.chromium.connect_over_cdp(CDP_URL)
        except Exception as e:
            print(f"[ERROR] Failed to attach over CDP: {e}")
            return

        # Reuse existing context
        contexts = browser.contexts
        context = contexts[0] if contexts else browser.new_context()
        page = context.new_page()

        try:
            for query in SEARCH_QUERIES:
                kw = query["keyword"]
                loc = query["location"]
                exp = query["experience"]

                if portal_choice in ["naukri", "both"]:
                    naukri_results = search_naukri(page, keyword=kw, location=loc, experience=exp, max_pages=1)
                    all_found_jobs.extend(naukri_results)
                    time.sleep(2)

                if portal_choice in ["linkedin", "both"]:
                    linkedin_results = search_linkedin(page, keyword=kw, location=loc, max_pages=1)
                    all_found_jobs.extend(linkedin_results)
                    time.sleep(2)

        finally:
            # Close only the temporary tab we opened, keep user's other Chrome tabs intact
            try:
                page.close()
            except Exception:
                pass

    save_results(all_found_jobs)

if __name__ == "__main__":
    choice = "both"
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["naukri", "linkedin", "both", "test"]:
            choice = arg

    if choice == "test":
        if test_cdp_connection():
            print("[OK] Chrome is ready for automation!")
        else:
            print("[X] Chrome is not running in debug mode.")
    else:
        run_job_search(portal_choice=choice)
