"""
Configuration for Automated Job Search & Resume Matching.
Tailored for Pavan Ravindra Kavade (.NET + Angular Full Stack Developer).
"""

import os

CANDIDATE_PROFILE = {
    "name": os.environ.get("CANDIDATE_NAME", "Full Stack AI Developer"),
    "email": os.environ.get("CANDIDATE_EMAIL", "candidate@example.com"),
    "phone": os.environ.get("CANDIDATE_PHONE", "+91 9876543210"),
    "total_experience_years": 5.5,
    "current_location": "Pune, Maharashtra",
    "preferred_locations": ["Pune", "Remote", "Hybrid", "Bangalore", "Hyderabad", "Mumbai"],
    "primary_skills": [
        "C#",
        ".NET Core",
        "ASP.NET Core",
        "ASP.NET",
        "Angular",
        "TypeScript",
        "Web API",
        "REST API",
        "SQL Server",
        "MS SQL",
        "Azure OpenAI",
        "Generative AI",
        "GenAI",
        "LLM",
        "AI Architecture",
        "AI Engineer"
    ],
    "secondary_skills": [
        "Azure",
        "Azure Speech Services",
        "Azure Table Storage",
        "Redis",
        "Redis Cache",
        "JavaScript",
        "HTML5",
        "CSS3",
        "Bootstrap",
        "Git",
        "Azure DevOps",
        "CI/CD",
        "Docker",
        "Entity Framework",
        "LINQ",
        "RAG",
        "Prompt Engineering",
        "Semantic Kernel",
        "LangChain",
        "AI Agents",
        "Agentic AI",
        "Solutions Architecture",
        "System Design"
    ]
}

# Search Queries targeted for .NET Core, Angular, and AI Development / Architect roles
SEARCH_QUERIES = [
    {
        "keyword": ".NET Core Angular",
        "location": "Pune",
        "experience": "5"
    },
    {
        "keyword": "Full Stack .NET Developer",
        "location": "Pune",
        "experience": "5"
    },
    {
        "keyword": "Generative AI Developer",
        "location": "Pune",
        "experience": "5"
    },
    {
        "keyword": "AI Engineer Azure OpenAI",
        "location": "Pune",
        "experience": "5"
    },
    {
        "keyword": "AI Architect",
        "location": "Pune",
        "experience": "5"
    },
    {
        "keyword": "AI Solutions Architect",
        "location": "Remote",
        "experience": "5"
    },
    {
        "keyword": "GenAI Developer",
        "location": "Remote",
        "experience": "5"
    },
    {
        "keyword": "ASP.NET Core Developer",
        "location": "Remote",
        "experience": "5"
    },
    {
        "keyword": "Senior .NET Developer",
        "location": "Pune",
        "experience": "5"
    }
]

# Chrome Remote Debugging Settings (IPv4 explicit)
CDP_URL = "http://127.0.0.1:9222"

# Automation Delays (in seconds) to behave like human browsing and avoid rate-limits
DELAYS = {
    "page_load": 4.0,
    "scroll_step": 1.5,
    "action_pause": 2.0
}
