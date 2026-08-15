"""
Database Layer for Job Application Tracker.
SQLite database storage for jobs, statuses, screening answers, and application history.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobs.db")

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Jobs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        portal TEXT NOT NULL,
        title TEXT NOT NULL,
        company TEXT NOT NULL,
        location TEXT,
        experience TEXT,
        salary TEXT,
        description TEXT,
        url TEXT UNIQUE NOT NULL,
        match_score REAL DEFAULT 0,
        matched_primary TEXT,
        matched_secondary TEXT,
        tags TEXT,
        status TEXT DEFAULT 'discovered', -- discovered, applied, action_required, screening, interviewing, offer, rejected, archived
        date_discovered TEXT,
        date_applied TEXT,
        notes TEXT,
        recruiter_contact TEXT,
        pending_questions TEXT
    );
    """)

    try:
        cursor.execute("ALTER TABLE jobs ADD COLUMN pending_questions TEXT;")
    except Exception:
        pass

    # Candidate Profile & Screening Answers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profile_qa (
        key TEXT PRIMARY KEY,
        question_pattern TEXT NOT NULL,
        answer TEXT NOT NULL,
        category TEXT DEFAULT 'general'
    );
    """)

    # Application Events / Activity Log
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER,
        event_type TEXT NOT NULL,
        details TEXT,
        timestamp TEXT,
        FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()

def upsert_job(job_data: Dict[str, Any]) -> Optional[int]:
    """
    Inserts a new job or updates match info if not yet applied.
    Returns the job ID if inserted/updated.
    """
    conn = get_connection()
    cursor = conn.cursor()

    now_str = datetime.now().isoformat()
    matched_p = json.dumps(job_data.get("matched_primary", []))
    matched_s = json.dumps(job_data.get("matched_secondary", []))
    tags_str = json.dumps(job_data.get("tags", []))

    try:
        cursor.execute("""
        INSERT INTO jobs (
            portal, title, company, location, experience, salary,
            description, url, match_score, matched_primary, matched_secondary,
            tags, status, date_discovered, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'discovered', ?, '')
        ON CONFLICT(url) DO UPDATE SET
            match_score = excluded.match_score,
            matched_primary = excluded.matched_primary,
            matched_secondary = excluded.matched_secondary,
            tags = excluded.tags
        WHERE jobs.status = 'discovered';
        """, (
            job_data.get("portal", "Unknown"),
            job_data.get("title", "Untitled"),
            job_data.get("company", "Confidential"),
            job_data.get("location", ""),
            job_data.get("experience", ""),
            job_data.get("salary", "Not disclosed"),
            job_data.get("description", ""),
            job_data.get("link", ""),
            job_data.get("match_score", 0.0),
            matched_p,
            matched_s,
            tags_str,
            now_str
        ))
        conn.commit()
        job_id = cursor.lastrowid
        return job_id
    except Exception as e:
        print(f"[DB Error] upsert_job: {e}")
        return None
    finally:
        conn.close()

def get_jobs(status: Optional[str] = None, portal: Optional[str] = None, min_score: float = 0.0, search: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM jobs WHERE match_score >= ?"
    params: List[Any] = [min_score]

    if status and status != 'all':
        query += " AND status = ?"
        params.append(status)

    if portal and portal != 'all':
        query += " AND portal = ?"
        params.append(portal)

    if search:
        query += " AND (title LIKE ? OR company LIKE ? OR location LIKE ? OR matched_primary LIKE ?)"
        search_pattern = f"%{search}%"
        params.extend([search_pattern, search_pattern, search_pattern, search_pattern])

    query += " ORDER BY match_score DESC, date_discovered DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        d = dict(r)
        try:
            d["matched_primary"] = json.loads(d["matched_primary"]) if d["matched_primary"] else []
        except Exception:
            d["matched_primary"] = []

        try:
            d["matched_secondary"] = json.loads(d["matched_secondary"]) if d["matched_secondary"] else []
        except Exception:
            d["matched_secondary"] = []

        try:
            d["tags"] = json.loads(d["tags"]) if d["tags"] else []
        except Exception:
            d["tags"] = []

        try:
            d["pending_questions"] = json.loads(d["pending_questions"]) if d.get("pending_questions") else []
        except Exception:
            d["pending_questions"] = []

        result.append(d)
    return result

def get_job_by_id(job_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    try:
        d["matched_primary"] = json.loads(d["matched_primary"]) if d["matched_primary"] else []
    except Exception:
        d["matched_primary"] = []
    try:
        d["matched_secondary"] = json.loads(d["matched_secondary"]) if d["matched_secondary"] else []
    except Exception:
        d["matched_secondary"] = []
    try:
        d["tags"] = json.loads(d["tags"]) if d["tags"] else []
    except Exception:
        d["tags"] = []
    try:
        d["pending_questions"] = json.loads(d["pending_questions"]) if d.get("pending_questions") else []
    except Exception:
        d["pending_questions"] = []
    return d

def update_job_status(job_id: int, status: str, notes: Optional[str] = None, pending_questions: Optional[List[str]] = None) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()

    questions_json = json.dumps(pending_questions) if pending_questions else None

    try:
        if status == 'applied':
            cursor.execute("""
            UPDATE jobs SET status = ?, date_applied = ?, notes = COALESCE(?, notes), pending_questions = NULL WHERE id = ?
            """, (status, now_str, notes, job_id))
        elif status == 'action_required':
            cursor.execute("""
            UPDATE jobs SET status = ?, notes = COALESCE(?, notes), pending_questions = COALESCE(?, pending_questions) WHERE id = ?
            """, (status, notes, questions_json, job_id))
        else:
            cursor.execute("""
            UPDATE jobs SET status = ?, notes = COALESCE(?, notes) WHERE id = ?
            """, (status, notes, job_id))

        # Log Activity
        cursor.execute("""
        INSERT INTO activity_log (job_id, event_type, details, timestamp) VALUES (?, ?, ?, ?)
        """, (job_id, f"Status updated to {status}", notes or "", now_str))

        conn.commit()
        return True
    except Exception as e:
        print(f"[DB Error] update_job_status: {e}")
        return False
    finally:
        conn.close()

def delete_job(job_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"[DB Error] delete_job: {e}")
        return False
    finally:
        conn.close()

def get_stats() -> Dict[str, int]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN status = 'discovered' THEN 1 ELSE 0 END) as discovered,
        SUM(CASE WHEN status = 'applied' THEN 1 ELSE 0 END) as applied,
        SUM(CASE WHEN status = 'action_required' THEN 1 ELSE 0 END) as action_required,
        SUM(CASE WHEN status = 'screening' THEN 1 ELSE 0 END) as screening,
        SUM(CASE WHEN status = 'interviewing' THEN 1 ELSE 0 END) as interviewing,
        SUM(CASE WHEN status = 'offer' THEN 1 ELSE 0 END) as offer,
        SUM(CASE WHEN match_score >= 70 THEN 1 ELSE 0 END) as high_matches
    FROM jobs;
    """)
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {"total": 0, "discovered": 0, "applied": 0, "action_required": 0, "screening": 0, "interviewing": 0, "offer": 0, "high_matches": 0}
    return {
        "total": row["total"] or 0,
        "discovered": row["discovered"] or 0,
        "applied": row["applied"] or 0,
        "action_required": row["action_required"] or 0,
        "screening": row["screening"] or 0,
        "interviewing": row["interviewing"] or 0,
        "offer": row["offer"] or 0,
        "high_matches": row["high_matches"] or 0
    }

# Initialize database tables on import
init_db()
