"""
Job Application Tracker & Chrome Co-Pilot Server.
FastAPI backend providing REST APIs and serving the responsive dashboard frontend.
"""

import os
import threading
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import database
import profile_manager
import copilot

app = FastAPI(title="Job Tracker & Chrome Co-Pilot", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory scan state
scan_state = {
    "is_scanning": False,
    "current_status": "Idle",
    "last_scan_time": None,
    "last_result": None
}

class JobStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None

class JobCreate(BaseModel):
    portal: str
    title: str
    company: str
    location: Optional[str] = ""
    experience: Optional[str] = ""
    salary: Optional[str] = ""
    description: Optional[str] = ""
    url: str
    match_score: Optional[float] = 0.0

class QARuleCreate(BaseModel):
    key: str
    question_pattern: str
    answer: str
    category: Optional[str] = "general"

# --- API Endpoints ---

@app.get("/api/status")
def get_system_status():
    chrome_info = copilot.check_chrome_status()
    stats = database.get_stats()
    return {
        "chrome": chrome_info,
        "stats": stats,
        "scan_state": scan_state
    }

@app.get("/api/jobs")
def list_jobs(
    status: Optional[str] = Query(None),
    portal: Optional[str] = Query(None),
    min_score: float = Query(0.0),
    search: Optional[str] = Query(None)
):
    jobs = database.get_jobs(status=status, portal=portal, min_score=min_score, search=search)
    return {"count": len(jobs), "jobs": jobs}

@app.get("/api/jobs/{job_id}")
def get_job(job_id: int):
    job = database.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.post("/api/jobs")
def create_job(job: JobCreate):
    job_id = database.upsert_job(job.dict())
    if not job_id:
        raise HTTPException(status_code=400, detail="Failed to save job")
    return {"success": True, "job_id": job_id}

@app.patch("/api/jobs/{job_id}")
def update_job(job_id: int, payload: JobStatusUpdate):
    success = database.update_job_status(job_id, payload.status, payload.notes)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update job status")
    return {"success": True, "message": f"Job status updated to {payload.status}"}

@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: int):
    success = database.delete_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete job")
    return {"success": True, "message": "Job deleted"}

def _background_scan_worker(portal: str):
    scan_state["is_scanning"] = True
    scan_state["current_status"] = f"Starting scan on {portal}..."
    try:
        def update_msg(msg):
            scan_state["current_status"] = msg

        result = copilot.run_live_scan(portal=portal, callback=update_msg)
        scan_state["last_result"] = result
        scan_state["current_status"] = f"Completed. Added {result.get('new_jobs_added', 0)} new jobs."
    except Exception as e:
        scan_state["current_status"] = f"Error during scan: {str(e)}"
    finally:
        scan_state["is_scanning"] = False

@app.post("/api/scan")
def trigger_scan(background_tasks: BackgroundTasks, portal: str = Query("both")):
    if scan_state["is_scanning"]:
        return {"success": False, "message": "A scan is already in progress"}

    background_tasks.add_task(_background_scan_worker, portal)
    return {"success": True, "message": f"Job scan initiated for {portal}"}

@app.get("/api/scan/status")
def get_scan_status():
    return scan_state

@app.post("/api/jobs/{job_id}/open")
def open_job_in_browser(job_id: int):
    job = database.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    res = copilot.open_job_in_chrome(job.get("url"))
    return res

@app.post("/api/jobs/{job_id}/apply")
def trigger_assisted_apply(job_id: int):
    res = copilot.assisted_apply_flow(job_id)
    return res

@app.get("/api/profile")
def get_candidate_profile():
    profile = profile_manager.load_profile()
    qa_rules = profile_manager.get_qa_rules()
    return {"profile": profile, "qa_rules": qa_rules}

@app.post("/api/profile")
def update_candidate_profile(data: Dict[str, Any]):
    profile_manager.save_profile(data)
    return {"success": True, "message": "Profile saved successfully"}

@app.post("/api/profile/qa")
def save_qa_rule(rule: QARuleCreate):
    profile_manager.save_qa_rule(rule.key, rule.question_pattern, rule.answer, rule.category)
    return {"success": True, "message": "Screening rule saved"}

# --- Static Frontend Serving ---
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Job Tracker API is running. UI files initializing..."}

if __name__ == "__main__":
    import uvicorn
    print("Starting JobPilot Web App at http://127.0.0.1:8000 ...")
    uvicorn.run("server:app", host="0.0.0.0", port=8000)
