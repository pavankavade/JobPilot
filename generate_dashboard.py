"""
Interactive HTML Job Dashboard Generator.
Renders a clean, responsive view of all scraped and matched jobs.
"""

import json
import os

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pavan Kavade - Job Matches</title>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #38bdf8;
            --badge-naukri: #0284c7;
            --badge-linkedin: #2563eb;
            --badge-high: #10b981;
            --border-color: #334155;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-color);
            color: var(--text-main);
            padding: 24px;
            line-height: 1.5;
        }
        .header {
            max-width: 1200px;
            margin: 0 auto 24px auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
        }
        .title h1 { font-size: 24px; font-weight: 700; color: #fff; }
        .title p { color: var(--text-muted); font-size: 14px; margin-top: 4px; }
        .search-bar {
            display: flex;
            gap: 12px;
            max-width: 1200px;
            margin: 0 auto 24px auto;
        }
        .search-input {
            flex: 1;
            padding: 10px 16px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            background: var(--card-bg);
            color: #fff;
            font-size: 15px;
            outline: none;
        }
        .job-grid {
            max-width: 1200px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
            gap: 20px;
        }
        .card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .card:hover {
            transform: translateY(-3px);
            border-color: var(--accent);
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
            gap: 8px;
        }
        .job-title {
            font-size: 17px;
            font-weight: 600;
            color: #fff;
            text-decoration: none;
        }
        .job-title:hover { color: var(--accent); }
        .match-badge {
            background: rgba(16, 185, 129, 0.15);
            color: var(--badge-high);
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 700;
            white-space: nowrap;
        }
        .company-meta {
            font-size: 14px;
            color: var(--text-muted);
            margin-bottom: 14px;
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            align-items: center;
        }
        .portal-tag {
            font-size: 11px;
            text-transform: uppercase;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
        }
        .portal-naukri { background: var(--badge-naukri); color: #fff; }
        .portal-linkedin { background: var(--badge-linkedin); color: #fff; }
        .skills-list {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 16px;
        }
        .skill-chip {
            background: rgba(56, 189, 248, 0.1);
            color: var(--accent);
            border: 1px solid rgba(56, 189, 248, 0.25);
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 12px;
        }
        .card-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 14px;
            border-top: 1px solid var(--border-color);
        }
        .salary {
            font-size: 13px;
            color: #fbbf24;
            font-weight: 500;
        }
        .apply-btn {
            background: var(--accent);
            color: #0f172a;
            font-weight: 600;
            font-size: 13px;
            padding: 8px 16px;
            border-radius: 6px;
            text-decoration: none;
            transition: opacity 0.2s ease;
        }
        .apply-btn:hover { opacity: 0.9; }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">
            <h1>Targeted Job Matches</h1>
            <p>Full Stack .NET, Angular & AI Solutions Architecture</p>
        </div>
        <div id="stats" style="color: var(--text-muted); font-size: 14px;"></div>
    </div>

    <div class="search-bar">
        <input type="text" id="filterInput" class="search-input" placeholder="Filter by company, skill, location..." onkeyup="filterCards()">
    </div>

    <div class="job-grid" id="jobGrid"></div>

    <script>
        const jobs = __JOBS_JSON__;
        const grid = document.getElementById('jobGrid');
        const stats = document.getElementById('stats');

        stats.innerText = `Total Roles: ${jobs.length}`;

        function render(jobsToRender) {
            grid.innerHTML = '';
            if (!jobsToRender.length) {
                grid.innerHTML = '<p style="color: #94a3b8;">No jobs found matching the filter.</p>';
                return;
            }

            jobsToRender.forEach(job => {
                const card = document.createElement('div');
                card.className = 'card';

                const portalClass = job.portal === 'Naukri' ? 'portal-naukri' : 'portal-linkedin';
                const skills = (job.matched_primary || []).concat(job.matched_secondary || []);
                const skillsHtml = skills.map(s => `<span class="skill-chip">${s}</span>`).join('');

                card.innerHTML = `
                    <div>
                        <div class="card-header">
                            <a href="${job.link}" target="_blank" class="job-title">${job.title}</a>
                            <span class="match-badge">${job.match_score || 0}% Match</span>
                        </div>
                        <div class="company-meta">
                            <span class="portal-tag ${portalClass}">${job.portal}</span>
                            <strong>${job.company || 'Direct Employer'}</strong>
                            <span>•</span>
                            <span>📍 ${job.location || 'Pune/Remote'}</span>
                        </div>
                        <div class="skills-list">${skillsHtml}</div>
                    </div>
                    <div class="card-footer">
                        <span class="salary">${job.salary && job.salary !== 'Not disclosed' ? job.salary : 'Salary upon application'}</span>
                        <a href="${job.link}" target="_blank" class="apply-btn">View & Apply →</a>
                    </div>
                `;
                grid.appendChild(card);
            });
        }

        function filterCards() {
            const query = document.getElementById('filterInput').value.toLowerCase();
            const filtered = jobs.filter(j => {
                const searchStr = `${j.title} ${j.company} ${j.location} ${(j.matched_primary || []).join(' ')}`.toLowerCase();
                return searchStr.includes(query);
            });
            render(filtered);
        }

        render(jobs);
    </script>
</body>
</html>
"""

def generate_html_dashboard():
    json_path = "jobs_latest.json"
    if not os.path.exists(json_path):
        print(f"[!] {json_path} not found. Run main.py first to scrape jobs.")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        jobs_data = json.load(f)

    html_content = HTML_TEMPLATE.replace("__JOBS_JSON__", json.dumps(jobs_data))
    output_html = "jobs_dashboard.html"

    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[SUCCESS] Dashboard generated at: {os.path.abspath(output_html)}")

if __name__ == "__main__":
    generate_html_dashboard()
