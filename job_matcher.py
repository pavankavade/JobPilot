"""
Job Matching & Scoring Engine.
Scores extracted job postings against Pavan's skill set and experience level.
"""

import re
from typing import Dict, Any, List
from config import CANDIDATE_PROFILE

def clean_text(text: str) -> str:
    if not text:
        return ""
    return text.lower().strip()

def calculate_match_score(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes a match percentage and lists matching/missing skills.
    """
    title = job.get("title", "")
    description = job.get("description", "")
    tags = " ".join(job.get("tags", []))
    combined_content = f"{title} {tags} {description}".lower()

    primary_skills = CANDIDATE_PROFILE["primary_skills"]
    secondary_skills = CANDIDATE_PROFILE["secondary_skills"]

    matched_primary: List[str] = []
    for skill in primary_skills:
        # Match as whole word / boundary
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, combined_content):
            matched_primary.append(skill)

    matched_secondary: List[str] = []
    for skill in secondary_skills:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, combined_content):
            matched_secondary.append(skill)

    # Core scoring logic
    primary_weight = 0.50
    secondary_weight = 0.50

    primary_score = (len(matched_primary) / max(min(len(primary_skills), 6), 1)) * 100
    secondary_score = (len(matched_secondary) / max(min(len(secondary_skills), 6), 1)) * 100

    # Title boost: Reward .NET, Angular, AI, and Architect roles heavily
    title_lower = title.lower()
    title_boost = 0
    is_ai_role = False
    is_architect_role = False

    # AI keywords check
    ai_keywords = ["ai", "genai", "generative ai", "openai", "azure openai", "llm", "rag", "agentic", "artificial intelligence", "prompt"]
    for kw in ai_keywords:
        if kw in title_lower.split() or f" {kw} " in f" {title_lower} " or kw in tags.lower():
            is_ai_role = True
            break

    # Architect / Tech Lead keywords check
    arch_keywords = ["architect", "solutions architect", "ai architect", "lead", "principal"]
    for kw in arch_keywords:
        if kw in title_lower:
            is_architect_role = True
            break

    if is_ai_role:
        title_boost += 35
    if is_architect_role:
        title_boost += 20
    if ".net" in title_lower or "c#" in title_lower or "asp.net" in title_lower:
        title_boost += 15
    if "angular" in title_lower or "full stack" in title_lower or "fullstack" in title_lower:
        title_boost += 10

    total_score = (primary_score * 0.4) + (secondary_score * 0.3) + title_boost
    total_score = min(99.0, max(25.0, round(total_score, 1)))

    return {
        "match_score": total_score,
        "is_ai_role": is_ai_role,
        "is_architect_role": is_architect_role,
        "matched_primary": matched_primary,
        "matched_secondary": matched_secondary,
        "matched_skills_count": len(matched_primary) + len(matched_secondary),
        "is_recommended": total_score >= 50.0
    }
