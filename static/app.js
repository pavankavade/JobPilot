// JobPilot Frontend Application Logic

let allJobs = [];
let activeModalJobId = null;
let scanCheckInterval = null;

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    loadDashboardData();
    checkChromeStatusNow();
    loadProfileData();

    // Poll status every 5 seconds
    setInterval(checkChromeStatusNow, 5000);
});

// Navigation Tabs
function initNavigation() {
    const navBtns = document.querySelectorAll(".nav-btn");
    navBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            navBtns.forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".tab-content").forEach(tab => tab.classList.remove("active"));

            btn.classList.add("active");
            const targetId = btn.getAttribute("data-tab");
            const targetTab = document.getElementById(targetId);
            if (targetTab) targetTab.classList.add("active");

            if (targetId === "pipeline-tab") {
                renderKanban();
            }
        });
    });
}

// Fetch and render all data
async function loadDashboardData() {
    try {
        const res = await fetch("/api/jobs");
        const data = await res.json();
        allJobs = data.jobs || [];

        updateStats();
        renderJobsFeed();
        renderKanban();
    } catch (err) {
        console.error("Error loading jobs data:", err);
    }
}

// Update Header Stats
function updateStats() {
    const total = allJobs.length;
    const high = allJobs.filter(j => j.match_score >= 70).length;
    const actionRequired = allJobs.filter(j => j.status === "action_required").length;
    const applied = allJobs.filter(j => j.status === "applied").length;
    const interview = allJobs.filter(j => ["screening", "interviewing", "offer"].includes(j.status)).length;
    const unapplied = allJobs.filter(j => j.status === "discovered").length;

    document.getElementById("stat-total").innerText = total;
    document.getElementById("stat-high").innerText = high;
    const actionEl = document.getElementById("stat-action");
    if (actionEl) actionEl.innerText = actionRequired;
    document.getElementById("stat-applied").innerText = applied;
    document.getElementById("stat-interview").innerText = interview;

    document.getElementById("feed-count").innerText = unapplied + actionRequired;
    document.getElementById("pipeline-count").innerText = total - unapplied;
}

// Filter and Render Job Matches Feed
function filterJobs() {
    renderJobsFeed();
}

function renderJobsFeed() {
    const grid = document.getElementById("jobs-list");
    const searchVal = document.getElementById("job-search-input").value.toLowerCase();
    const portalVal = document.getElementById("portal-filter").value;
    const scoreVal = parseFloat(document.getElementById("score-filter").value);
    const statusVal = document.getElementById("status-filter").value;

    const filtered = allJobs.filter(j => {
        if (portalVal !== "all" && j.portal !== portalVal) return false;
        if (statusVal !== "all" && j.status !== statusVal) return false;
        if (j.match_score < scoreVal) return false;

        if (searchVal) {
            const combined = `${j.title} ${j.company} ${j.location} ${(j.matched_primary || []).join(" ")}`.toLowerCase();
            if (!combined.includes(searchVal)) return false;
        }
        return true;
    });

    if (!filtered.length) {
        grid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 48px; color: var(--text-muted);">
                <p style="font-size: 16px; margin-bottom: 8px;">No matching jobs found with current filters.</p>
                <button class="btn btn-primary btn-sm" onclick="triggerScan()">⚡ Run a Chrome Scan Now</button>
            </div>
        `;
        return;
    }

    grid.innerHTML = filtered.map(job => {
        let scoreClass = "match-low";
        if (job.match_score >= 70) scoreClass = "match-high";
        else if (job.match_score >= 50) scoreClass = "match-mid";

        const portalClass = job.portal === "Naukri" ? "portal-naukri" : "portal-linkedin";
        
        const primaryChips = (job.matched_primary || []).map(s => `<span class="skill-tag skill-primary">${s}</span>`).join("");
        const secondaryChips = (job.matched_secondary || []).slice(0, 3).map(s => `<span class="skill-tag skill-secondary">${s}</span>`).join("");

        const isApplied = job.status === "applied";
        const isActionRequired = job.status === "action_required";

        const questionsAlertHtml = (isActionRequired && job.pending_questions && job.pending_questions.length > 0) ? `
            <div class="questions-alert">
                <div class="questions-alert-header">⚠️ Questions Prompted (Requires Your Review):</div>
                <ul class="questions-list">
                    ${job.pending_questions.map(q => `<li>${escapeHtml(q)}</li>`).join("")}
                </ul>
            </div>
        ` : '';

        return `
            <div class="job-card" style="${isActionRequired ? 'border-color: rgba(245, 158, 11, 0.5);' : ''}">
                <div>
                    <div class="job-header">
                        <a href="${job.url}" target="_blank" class="job-title">${escapeHtml(job.title)}</a>
                        <span class="match-badge ${scoreClass}">${job.match_score}% Match</span>
                    </div>

                    <div class="job-meta">
                        <span class="portal-badge ${portalClass}">${job.portal}</span>
                        <strong>${escapeHtml(job.company)}</strong>
                        <span>•</span>
                        <span>📍 ${escapeHtml(job.location || 'Pune / Remote')}</span>
                        ${job.experience ? `<span>• 💼 ${escapeHtml(job.experience)}</span>` : ''}
                        ${isActionRequired ? `<span style="color: #f59e0b; font-weight: 700; font-size: 11px;">[⚠️ Questions Prompted]</span>` : ''}
                    </div>

                    <div class="skills-wrapper">
                        ${primaryChips}
                        ${secondaryChips}
                    </div>

                    ${questionsAlertHtml}
                </div>

                <div class="job-footer">
                    <span class="job-salary">${job.salary && job.salary !== 'Not disclosed' ? escapeHtml(job.salary) : 'Salary undisclosed'}</span>
                    
                    <div class="job-actions">
                        <button class="btn btn-secondary btn-sm" onclick="openInChrome(${job.id})" title="Open job in your active Chrome window">
                            🌐 Open
                        </button>
                        <button class="btn ${isActionRequired ? 'btn-secondary' : 'btn-primary'} btn-sm" onclick="applyViaChrome(${job.id})" title="Auto-open and assist in applying">
                            ${isActionRequired ? '🔍 Review & Apply' : (isApplied ? '✓ Applied' : '⚡ 1-Click Apply')}
                        </button>
                        <button class="btn btn-secondary btn-sm" onclick="openJobModal(${job.id})" title="Notes & Stage">
                            ⚙️
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join("");
}

// Render Kanban Board
function renderKanban() {
    const stages = ["discovered", "action_required", "applied", "screening", "interviewing", "offer", "rejected"];
    
    stages.forEach(stage => {
        const col = document.getElementById(`col-${stage}`);
        const countEl = document.getElementById(`count-${stage}`);
        if (!col) return;

        const stageJobs = allJobs.filter(j => j.status === stage);
        if (countEl) countEl.innerText = stageJobs.length;

        if (!stageJobs.length) {
            col.innerHTML = `<p style="color: var(--text-dim); font-size: 12px; text-align: center; margin-top: 20px;">No jobs in this stage</p>`;
            return;
        }

        col.innerHTML = stageJobs.map(job => `
            <div class="kanban-card" onclick="openJobModal(${job.id})" style="${job.status === 'action_required' ? 'border-color: rgba(245, 158, 11, 0.4);' : ''}">
                <div class="kc-title">${escapeHtml(job.title)}</div>
                <div class="kc-company">${escapeHtml(job.company)} • <span style="color: var(--accent);">${job.match_score}%</span></div>
                ${job.pending_questions && job.pending_questions.length > 0 ? `<div style="color: #f59e0b; font-size: 11px; margin-bottom: 6px;">⚠️ ${job.pending_questions.length} question(s) prompted</div>` : ''}
                <div class="kc-footer">
                    <span>${job.portal}</span>
                    <span>${job.date_applied ? 'Applied ' + formatDate(job.date_applied) : 'Found ' + formatDate(job.date_discovered)}</span>
                </div>
            </div>
        `).join("");
    });
}

// Chrome CDP Status Check
async function checkChromeStatusNow() {
    try {
        const res = await fetch("/api/status");
        const data = await res.json();
        const pill = document.getElementById("chrome-status-pill");
        const text = document.getElementById("chrome-status-text");

        if (data.chrome && data.chrome.connected) {
            pill.className = "status-pill status-connected";
            text.innerText = "Chrome Connected (Port 9222)";
        } else {
            pill.className = "status-pill status-disconnected";
            text.innerText = "Chrome Disconnected (Click to Fix)";
        }

        // Check if background scan is active
        if (data.scan_state && data.scan_state.is_scanning) {
            showScanProgress(data.scan_state.current_status);
        } else if (document.getElementById("scan-progress-bar").classList.contains("active")) {
            hideScanProgress();
            loadDashboardData();
        }
    } catch (e) {
        console.error("Status check failed:", e);
    }
}

// Trigger Live Scan
async function triggerScan() {
    const btn = document.getElementById("scan-btn");
    btn.disabled = true;

    try {
        const res = await fetch("/api/scan?portal=both", { method: "POST" });
        const data = await res.json();

        if (data.success) {
            showScanProgress("Initiated scan on Naukri & LinkedIn...");
            if (!scanCheckInterval) {
                scanCheckInterval = setInterval(pollScanStatus, 2000);
            }
        } else {
            alert(data.message || "Failed to start scan");
            btn.disabled = false;
        }
    } catch (err) {
        alert("Scan trigger error: " + err);
        btn.disabled = false;
    }
}

async function pollScanStatus() {
    try {
        const res = await fetch("/api/scan/status");
        const data = await res.json();

        if (data.is_scanning) {
            showScanProgress(data.current_status || "Scanning...");
        } else {
            clearInterval(scanCheckInterval);
            scanCheckInterval = null;
            hideScanProgress();
            document.getElementById("scan-btn").disabled = false;
            loadDashboardData();
        }
    } catch (e) {
        console.error("Poll scan error:", e);
    }
}

function showScanProgress(msg) {
    const bar = document.getElementById("scan-progress-bar");
    bar.classList.remove("hidden");
    bar.classList.add("active");
    document.getElementById("scan-status-text").innerText = msg;
}

function hideScanProgress() {
    const bar = document.getElementById("scan-progress-bar");
    bar.classList.add("hidden");
    bar.classList.remove("active");
}

// Open Job in Chrome
async function openInChrome(jobId) {
    try {
        const res = await fetch(`/api/jobs/${jobId}/open`, { method: "POST" });
        const data = await res.json();
        if (!data.success) {
            alert(data.error || "Could not open in Chrome. Make sure launch_chrome.bat is running.");
        }
    } catch (e) {
        alert("Error: " + e);
    }
}

// Assisted Apply Flow
async function applyViaChrome(jobId) {
    const btn = event.target;
    const oldText = btn.innerText;
    btn.innerText = "⏳ Applying...";
    btn.disabled = true;

    try {
        const res = await fetch(`/api/jobs/${jobId}/apply`, { method: "POST" });
        const data = await res.json();
        if (data.success) {
            btn.innerText = "✓ Opened";
            loadDashboardData();
        } else {
            alert(data.error || "Assisted apply failed");
            btn.innerText = oldText;
            btn.disabled = false;
        }
    } catch (e) {
        alert("Apply error: " + e);
        btn.innerText = oldText;
        btn.disabled = false;
    }
}

// Job Edit Modal
function openJobModal(jobId) {
    activeModalJobId = jobId;
    const job = allJobs.find(j => j.id === jobId);
    if (!job) return;

    document.getElementById("modal-job-title").innerText = job.title;
    document.getElementById("modal-job-company").innerText = `${job.company} • ${job.portal}`;
    document.getElementById("modal-job-status").value = job.status || "discovered";
    document.getElementById("modal-job-notes").value = job.notes || "";

    document.getElementById("job-modal").classList.remove("hidden");
}

function closeJobModal() {
    document.getElementById("job-modal").classList.add("hidden");
    activeModalJobId = null;
}

async function saveJobModal() {
    if (!activeModalJobId) return;

    const status = document.getElementById("modal-job-status").value;
    const notes = document.getElementById("modal-job-notes").value;

    try {
        const res = await fetch(`/api/jobs/${activeModalJobId}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status, notes })
        });
        const data = await res.json();
        if (data.success) {
            closeJobModal();
            loadDashboardData();
        }
    } catch (e) {
        alert("Save failed: " + e);
    }
}

async function deleteCurrentModalJob() {
    if (!activeModalJobId || !confirm("Are you sure you want to delete this job?")) return;

    try {
        const res = await fetch(`/api/jobs/${activeModalJobId}`, { method: "DELETE" });
        const data = await res.json();
        if (data.success) {
            closeJobModal();
            loadDashboardData();
        }
    } catch (e) {
        alert("Delete failed: " + e);
    }
}

// Profile & Q&A Rules
async function loadProfileData() {
    try {
        const res = await fetch("/api/profile");
        const data = await res.json();
        const p = data.profile || {};

        document.getElementById("prof-name").value = p.name || "";
        document.getElementById("prof-email").value = p.email || "";
        document.getElementById("prof-phone").value = p.phone || "";
        document.getElementById("prof-location").value = p.location || "";
        document.getElementById("prof-exp").value = p.total_experience || "";
        document.getElementById("prof-notice").value = p.notice_period || "";
        document.getElementById("prof-current-ctc").value = p.current_ctc || "";
        document.getElementById("prof-expected-ctc").value = p.expected_ctc || "";
        document.getElementById("prof-resume").value = p.resume_path || "";

        // Render Q&A table
        const tbody = document.getElementById("qa-table-body");
        tbody.innerHTML = (data.qa_rules || []).map(r => `
            <tr>
                <td><code>${escapeHtml(r.question_pattern)}</code></td>
                <td><strong>${escapeHtml(r.answer)}</strong></td>
                <td><span class="skill-tag skill-secondary">${r.category}</span></td>
            </tr>
        `).join("");
    } catch (e) {
        console.error("Load profile error:", e);
    }
}

async function saveProfile(e) {
    e.preventDefault();
    const updated = {
        name: document.getElementById("prof-name").value,
        email: document.getElementById("prof-email").value,
        phone: document.getElementById("prof-phone").value,
        location: document.getElementById("prof-location").value,
        total_experience: document.getElementById("prof-exp").value,
        notice_period: document.getElementById("prof-notice").value,
        current_ctc: document.getElementById("prof-current-ctc").value,
        expected_ctc: document.getElementById("prof-expected-ctc").value,
        resume_path: document.getElementById("prof-resume").value
    };

    try {
        const res = await fetch("/api/profile", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(updated)
        });
        const data = await res.json();
        if (data.success) {
            alert("Candidate profile saved successfully!");
        }
    } catch (e) {
        alert("Error saving profile: " + e);
    }
}

async function addQARule(e) {
    e.preventDefault();
    const key = document.getElementById("qa-key").value;
    const pattern = document.getElementById("qa-pattern").value;
    const answer = document.getElementById("qa-answer").value;

    try {
        const res = await fetch("/api/profile/qa", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ key, question_pattern: pattern, answer, category: "custom" })
        });
        const data = await res.json();
        if (data.success) {
            document.getElementById("add-qa-form").reset();
            loadProfileData();
        }
    } catch (e) {
        alert("Error adding QA rule: " + e);
    }
}

// Chrome Modal
function showChromeModal() {
    const modal = document.getElementById("chrome-modal");
    const body = document.getElementById("chrome-modal-body");
    const isConnected = document.getElementById("chrome-status-pill").classList.contains("status-connected");

    if (isConnected) {
        body.innerHTML = `
            <div style="color: #34d399; font-weight: 600; margin-bottom: 12px;">✓ Chrome Remote Debugging is Active!</div>
            <p style="color: var(--text-muted); font-size: 13.5px;">Port <code>9222</code> is listening and connected to your active Chrome browser with your logged-in profiles.</p>
        `;
    } else {
        body.innerHTML = `
            <div style="color: #f87171; font-weight: 600; margin-bottom: 12px;">✕ Chrome is not running in Remote Debugging Mode</div>
            <p style="color: var(--text-muted); font-size: 13.5px; margin-bottom: 16px;">To connect your real Chrome with all logged-in sites:</p>
            <ol style="margin-left: 20px; color: var(--text-muted); font-size: 13.5px; line-height: 1.8;">
                <li>Double click <code>launch_chrome.bat</code> in <code>D:\\git\\jobsearch</code>.</li>
                <li>It will automatically close any old background Chrome instances and start Chrome with port 9222 enabled.</li>
                <li>Click <strong>"Re-Check Connection"</strong> below.</li>
            </ol>
        `;
    }
    modal.classList.remove("hidden");
}

function closeChromeModal() {
    document.getElementById("chrome-modal").classList.add("hidden");
}

function closeModalOnBackdrop(e) {
    if (e.target.classList.contains("modal-overlay")) {
        e.target.classList.add("hidden");
    }
}

// Utility Helpers
function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function formatDate(isoStr) {
    if (!isoStr) return "";
    try {
        const d = new Date(isoStr);
        return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    } catch {
        return isoStr;
    }
}
