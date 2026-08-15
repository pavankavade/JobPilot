"""
Profile & Auto-Fill Question/Answer Memory Manager.
Maintains standard and custom screening answers for automated/assisted applying.
"""

import json
import os
from typing import Dict, Any, List
from database import get_connection

DEFAULT_PROFILE = {
    "name": os.environ.get("CANDIDATE_NAME", "Full Stack AI Developer"),
    "email": os.environ.get("CANDIDATE_EMAIL", "candidate@example.com"),
    "phone": os.environ.get("CANDIDATE_PHONE", "+91 9876543210"),
    "location": "Pune, Maharashtra, India",
    "total_experience": "5.5 Years",
    "current_company": "Technology Services",
    "current_designation": "Associate / AI Developer",
    "notice_period": "30 Days (Negotiable)",
    "serving_notice": "No",
    "current_ctc": "Negotiable",
    "expected_ctc": "Negotiable",
    "resume_path": os.environ.get("RESUME_PATH", "resume.pdf"),
    "linkedin_url": "https://www.linkedin.com",
    "github_url": "https://github.com",
    "portfolio_url": "",
    "work_authorization": "Yes, authorized to work in India",
    "willing_to_relocate": "Yes (Pune, Bangalore, Hyderabad, Remote)"
}

DEFAULT_QA_RULES = [
    {"key": "exp_net_core", "question_pattern": r"(experience.*\.net|asp\.net|\.net core)", "answer": "5.5", "category": "skills"},
    {"key": "exp_csharp", "question_pattern": r"(experience.*c#|c-sharp)", "answer": "5.5", "category": "skills"},
    {"key": "exp_angular", "question_pattern": r"(experience.*angular)", "answer": "4", "category": "skills"},
    {"key": "exp_sql", "question_pattern": r"(experience.*sql|ms sql|database)", "answer": "5", "category": "skills"},
    {"key": "exp_azure", "question_pattern": r"(experience.*azure|cloud)", "answer": "2", "category": "skills"},
    {"key": "notice_period", "question_pattern": r"(notice period|how soon.*join|availability)", "answer": "30 days", "category": "general"},
    {"key": "current_location", "question_pattern": r"(current location|city|reside)", "answer": "Pune", "category": "general"},
    {"key": "work_auth", "question_pattern": r"(authorized to work|sponsorship|visa)", "answer": "Yes", "category": "general"},
    {"key": "remote_pref", "question_pattern": r"(willing to work remote|hybrid|relocate)", "answer": "Yes", "category": "general"}
]

PROFILE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profile.json")

def load_profile() -> Dict[str, Any]:
    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    save_profile(DEFAULT_PROFILE)
    return DEFAULT_PROFILE

def save_profile(data: Dict[str, Any]):
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_qa_rules() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profile_qa")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        # Seed default rules
        conn = get_connection()
        c = conn.cursor()
        for r in DEFAULT_QA_RULES:
            c.execute("INSERT OR REPLACE INTO profile_qa (key, question_pattern, answer, category) VALUES (?, ?, ?, ?)",
                      (r["key"], r["question_pattern"], r["answer"], r["category"]))
        conn.commit()
        conn.close()
        return DEFAULT_QA_RULES

    return [dict(r) for r in rows]

def save_qa_rule(key: str, question_pattern: str, answer: str, category: str = "general"):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO profile_qa (key, question_pattern, answer, category) VALUES (?, ?, ?, ?)",
              (key, question_pattern, answer, category))
    conn.commit()
    conn.close()
