from playwright.sync_api import sync_playwright

def test_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            headless=True
        )
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        print("[*] Navigating to http://127.0.0.1:8000 ...")
        page.goto("http://127.0.0.1:8000", wait_until="networkidle")

        title = page.title()
        print(f"[*] Page Title: {title}")

        total_stat = page.inner_text("#stat-total")
        high_stat = page.inner_text("#stat-high")
        cards = page.query_selector_all(".job-card")
        
        print(f"[*] Stat Total Count: {total_stat}")
        print(f"[*] High Match Count: {high_stat}")
        print(f"[*] Visible Job Cards: {len(cards)}")

        if cards:
            first_title = page.inner_text(".job-card .job-title")
            first_comp = page.inner_text(".job-card .job-meta strong")
            first_match = page.inner_text(".job-card .match-badge")
            print(f"[*] Sample Card: '{first_title}' at '{first_comp}' ({first_match})")

        # Test switching to Pipeline tab
        print("[*] Testing Applications Pipeline tab...")
        page.click("button[data-tab='pipeline-tab']")
        kanban_cols = len(page.query_selector_all(".kanban-col"))
        print(f"[*] Kanban Columns: {kanban_cols}")

        # Test switching to Profile tab
        print("[*] Testing Auto-Fill & Profile tab...")
        page.click("button[data-tab='profile-tab']")
        prof_name = page.input_value("#prof-name")
        print(f"[*] Loaded Profile Name: {prof_name}")

        print(f"[*] Total Console Errors: {len(console_errors)}")
        if console_errors:
            print("Console Errors:", console_errors)

        screenshot_path = "D:/git/jobsearch/ui_test_screenshot.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"[SUCCESS] UI Test completed! Screenshot saved to {screenshot_path}")
        browser.close()

if __name__ == "__main__":
    test_ui()
