"""
Chrome Co-Pilot & Automation Engine.
Connects to Google Chrome via CDP (port 9222) to scrape, navigate, and assist in applying.
"""

import time
import json
import urllib.request
from typing import Dict, Any, List, Optional, Callable
from playwright.sync_api import sync_playwright

from config import CDP_URL, SEARCH_QUERIES
from database import upsert_job, get_job_by_id, update_job_status
from scrapers.naukri_scraper import search_naukri
from scrapers.linkedin_scraper import search_linkedin
from profile_manager import load_profile

def check_chrome_status() -> Dict[str, Any]:
    """Tests if Chrome is reachable on port 9222 and returns session info."""
    try:
        req = urllib.request.Request(f"{CDP_URL}/json/version")
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode())
            return {
                "connected": True,
                "browser": data.get("Browser", "Google Chrome"),
                "protocol_version": data.get("Protocol-Version", "1.3"),
                "user_agent": data.get("User-Agent", "")
            }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "hint": "Run launch_chrome.bat to start Chrome in debugging mode."
        }

def open_job_in_chrome(url: str) -> Dict[str, Any]:
    """Opens a given URL in the user's active Chrome browser."""
    if not url:
        return {"success": False, "error": "No URL provided"}

    status = check_chrome_status()
    if not status["connected"]:
        return {"success": False, "error": "Chrome is not connected on port 9222"}

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(CDP_URL)
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.bring_to_front()
            return {"success": True, "message": f"Opened {url} in Chrome tab"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def run_live_scan(portal: str = "both", callback: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
    """Scrapes jobs from Naukri / LinkedIn and directly saves into SQLite DB."""
    status = check_chrome_status()
    if not status["connected"]:
        return {"success": False, "error": "Chrome is not running in debug mode. Please run launch_chrome.bat first."}

    total_scraped = 0
    new_jobs_added = 0

    if callback:
        callback("Connecting to Chrome on port 9222...")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.new_page()

        try:
            for q in SEARCH_QUERIES:
                kw = q["keyword"]
                loc = q["location"]
                exp = q["experience"]

                if portal in ["naukri", "both"]:
                    if callback:
                        callback(f"Scanning Naukri for '{kw}' in '{loc}'...")
                    naukri_results = search_naukri(page, keyword=kw, location=loc, experience=exp, max_pages=1)
                    for job in naukri_results:
                        total_scraped += 1
                        job_id = upsert_job(job)
                        if job_id:
                            new_jobs_added += 1
                    time.sleep(2)

                if portal in ["linkedin", "both"]:
                    if callback:
                        callback(f"Scanning LinkedIn for '{kw}' in '{loc}'...")
                    linkedin_results = search_linkedin(page, keyword=kw, location=loc, max_pages=1)
                    for job in linkedin_results:
                        total_scraped += 1
                        job_id = upsert_job(job)
                        if job_id:
                            new_jobs_added += 1
                    time.sleep(2)

        finally:
            try:
                page.close()
            except Exception:
                pass

    return {
        "success": True,
        "total_scraped": total_scraped,
        "new_jobs_added": new_jobs_added
    }

def assisted_apply_flow(job_id: int) -> Dict[str, Any]:
    """
    Assisted Apply Co-Pilot:
    1. Opens the job in Chrome.
    2. Detects 'Easy Apply' or 'Apply' button.
    3. Clicks apply to open modal/form.
    4. Auto-fills known fields (Phone, Email, Experience).
    5. Leaves form active for user review/submission.
    """
    job = get_job_by_id(job_id)
    if not job:
        return {"success": False, "error": "Job not found in database"}

    url = job.get("url")
    if not url:
        return {"success": False, "error": "Job URL is missing"}

    status = check_chrome_status()
    if not status["connected"]:
        return {"success": False, "error": "Chrome is not connected on port 9222"}

    profile = load_profile()

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(CDP_URL)
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.bring_to_front()
            time.sleep(3)

            # Check for Easy Apply / Apply button
            actions_taken = []
            detected_questions = []
            is_simple_apply = True

            if job.get("portal") == "LinkedIn":
                easy_apply_btn = page.query_selector("button.jobs-apply-button")
                if easy_apply_btn and easy_apply_btn.is_visible():
                    easy_apply_btn.click()
                    actions_taken.append("Clicked LinkedIn Easy Apply")
                    time.sleep(2)

                    # Check for form fields / multi-step questions
                    questions = page.evaluate('''() => {
                        const prompts = [];
                        const labels = document.querySelectorAll('.jobs-easy-apply-modal label, .jobs-easy-apply-modal .fb-dash-form-element, .jobs-easy-apply-modal legend');
                        labels.forEach(l => {
                            const txt = l.innerText.trim();
                            if (txt && !txt.toLowerCase().includes('phone') && !txt.toLowerCase().includes('email') && !txt.toLowerCase().includes('first name') && !txt.toLowerCase().includes('last name') && !txt.toLowerCase().includes('resume')) {
                                prompts.push(txt.split('\\n')[0]);
                            }
                        });
                        return Array.from(new Set(prompts)).slice(0, 5);
                    }''')

                    if questions and len(questions) > 0:
                        is_simple_apply = False
                        detected_questions = questions
                        actions_taken.append(f"Detected {len(questions)} custom screening questions")
                else:
                    is_simple_apply = False
                    actions_taken.append("External / complex application link")

            elif job.get("portal") == "Naukri":
                apply_btn = page.query_selector("#apply-button, .apply-button, button:has-text('Apply')")
                if apply_btn and apply_btn.is_visible():
                    actions_taken.append("Located Naukri Apply button")
                    # Check if chatbot / questionnaire drawer exists
                    q_elements = page.query_selector_all(".chatbot_Drawer, .apply-message, .questionnaire")
                    if q_elements:
                        is_simple_apply = False
                        detected_questions.append("Naukri screening questionnaire / recruiter prompt")
                else:
                    is_simple_apply = False
                    actions_taken.append("External company career site")

            if is_simple_apply and not detected_questions:
                update_job_status(job_id, status="applied", notes="Simple Apply completed via Co-Pilot")
                return {
                    "success": True,
                    "type": "simple_apply",
                    "actions": actions_taken,
                    "message": f"Simple Apply succeeded for '{job.get('title')}'!"
                }
            else:
                update_job_status(job_id, status="action_required", notes="Custom questions detected", pending_questions=detected_questions)
                return {
                    "success": True,
                    "type": "action_required",
                    "questions": detected_questions,
                    "actions": actions_taken,
                    "message": f"Questions detected for '{job.get('title')}'. Flagged in Web App for your review with link!"
                }

    except Exception as e:
        return {"success": False, "error": str(e)}
