# JobPilot ⚡

**JobPilot** is an automated job discovery, relevance scoring, and application tracking co-pilot. It connects directly to your live Google Chrome session via the Chrome DevTools Protocol (CDP) to discover, match, track, and assist in applying to high-matching roles across platforms like **LinkedIn** and **Naukri**.

---

## ✨ Features

- **Chrome DevTools Protocol (CDP) Integration:** Runs side-by-side with your active browser sessions without credential sharing or headless bot blocks.
- **Intelligent Resume Matching Engine:** Scores roles (0–100%) against primary/secondary tech stacks (e.g., .NET Core, Angular, SQL Server, Azure OpenAI, GenAI Architecture).
- **Application Triage:** Automatically detects simple 1-click applies vs. complex multi-step questionnaires, flagging jobs with screening questions for human review.
- **Interactive Kanban Pipeline & Dashboard:** Full CRM tracking (*Discovered → Needs Review → Applied → Screening → Interviewing → Offer*).
- **Automated Screening Q&A Memory:** Remembers answers to repetitive portal screening questions (Notice period, CTC, experience per skill).

---

## 📁 Repository Structure

```
JobPilot/
├── static/                   # Modern Web Application UI (HTML5, CSS3, Vanilla JS)
│   ├── index.html
│   ├── style.css
│   └── app.js
├── scrapers/                 # Portal Scraper Engines
│   ├── naukri_scraper.py
│   └── linkedin_scraper.py
├── server.py                 # FastAPI Web & REST Backend
├── database.py               # SQLite Database & Activity Logger (jobs.db)
├── copilot.py                # Chrome CDP Automation & Navigation Engine
├── job_matcher.py            # Tech Stack & Title Scoring Engine
├── profile_manager.py        # Candidate Profile & Q&A Memory Store
├── config.py                 # Search Queries & Target Locations
├── run.bat                   # 1-Click All-in-One Launcher
├── launch_chrome.bat         # Chrome Debug Mode Launcher (Port 9222)
└── start_app.bat             # Web Server Launcher (Port 8000)
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- Google Chrome
- Install dependencies:
```bash
pip install fastapi uvicorn playwright pydantic
```

### 2. Launching JobPilot
Run the all-in-one launcher on Windows:
```cmd
run.bat
```

Or start components individually:
1. **Launch Debug Chrome:**
   ```cmd
   launch_chrome.bat
   ```
2. **Launch Server:**
   ```cmd
   python server.py
   ```
3. Open `http://localhost:8000` in your browser.

---

## ⚙️ Configuration

Custom search queries, target locations, and matching weights can be configured in `config.py` and through the **Auto-Fill & Profile** tab in the Web App.

---

## 📄 License
MIT License
