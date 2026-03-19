"""
Rule-based fallback analysis service.
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict
from urllib.parse import quote

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def _load_data():
    with open(DATA_DIR / "job_roles.json") as f:
        roles_db = json.load(f)
    with open(DATA_DIR / "skills_taxonomy.json") as f:
        taxonomy = json.load(f)
    return roles_db, taxonomy["aliases"]


def _normalize(skills: list, aliases: Dict[str, str]) -> set:
    """Lowercase and resolve aliases. 'JS' → 'javascript', 'k8s' → 'kubernetes', etc."""
    normalized = set()
    for s in skills:
        key = s.strip().lower()
        normalized.add(aliases.get(key, key))
    return normalized


SKILL_LEARNING_DAYS: Dict[str, int] = {
    # Core tools
    "git": 1, "bash": 2, "linux": 5, "monitoring": 5, "ci/cd": 4,
    # Web & Frontend
    "html/css": 3, "javascript": 7, "typescript": 5, "react": 7, "nodejs": 5,
    "nextjs": 5, "vuejs": 5, "redux": 4, "webpack": 3, "accessibility": 3,
    # Backend & APIs
    "rest apis": 3, "grpc": 5, "celery": 3,
    # Cloud & Infrastructure
    "docker": 3, "aws": 10, "kubernetes": 10, "terraform": 8, "serverless": 5,
    "ansible": 5, "prometheus": 3, "grafana": 3, "virtualization": 4,
    "windows server": 5, "active directory": 4, "powershell": 5,
    "cloud networking": 5, "backup solutions": 3,
    # Databases
    "sql": 5, "postgresql": 5, "redis": 3, "mongodb": 4, "snowflake": 5,
    "bigquery": 4, "oracle": 7, "database design": 5, "performance tuning": 5,
    "backup and recovery": 3, "replication": 3, "query optimization": 4,
    "data warehousing": 5, "dax": 4, "looker": 3,
    # Data & Analytics
    "python": 7, "spark": 14, "airflow": 7, "kafka": 10, "data pipelines": 7,
    "pandas": 5, "numpy": 3, "statistics": 7, "data visualization": 5,
    "excel": 3, "tableau": 4, "power bi": 4, "r": 7, "jupyter": 1,
    "scikit-learn": 5, "business intelligence": 7, "reporting": 2,
    "etl processes": 5, "dbt": 4, "feature engineering": 5,
    # AI/ML
    "machine learning": 14, "deep learning": 14, "pytorch": 10, "tensorflow": 10,
    "mlflow": 4, "hugging face": 5, "transformers": 7, "bert": 5, "llms": 7,
    "cuda": 7, "distributed training": 7, "research skills": 5, "mathematics": 10,
    "paper implementation": 7,
    # Computer Vision & NLP
    "opencv": 7, "image processing": 5, "object detection": 7, "data augmentation": 3,
    "nlp": 10, "text processing": 3, "spacy": 3, "computer vision": 10,
    # Security
    "security fundamentals": 10, "networking": 7, "penetration testing": 10,
    "siem": 7, "cryptography": 10, "incident response": 5, "ethical hacking": 10,
    "metasploit": 5, "burp suite": 5, "kali linux": 5, "web vulnerabilities": 7,
    "scripting": 3,
    # Networking
    "cisco": 7, "routing": 5, "switching": 5, "tcp/ip": 5, "firewalls": 5,
    "network security": 7, "vpn": 3, "sdn": 7, "automation": 5,
    # Languages
    "c": 10, "c++": 14, "c#": 7, "rust": 14, "golang": 10, "assembly": 14,
    "matlab": 7, "java": 10,
    # Embedded & Hardware
    "microcontrollers": 7, "rtos": 7, "electronics": 10, "arm": 5, "fpga": 14,
    "communication protocols": 5, "embedded systems": 10, "pcb design": 10,
    "debugging": 3, "profiling": 3, "operating systems": 10,
    "memory management": 5, "algorithms": 14, "kernel development": 14,
    # Game & AR/VR
    "unity": 7, "unreal engine": 10, "game engines": 7, "c#": 7,
    "opengl": 10, "shaders": 7, "blender": 7, "physics simulation": 5,
    "multiplayer networking": 7, "3d mathematics": 7, "openxr": 5,
    "webxr": 5, "threejs": 5, "spatial computing": 7,
    # Blockchain
    "solidity": 7, "ethereum": 5, "web3": 5, "smart contracts": 7,
    "hardhat": 3, "truffle": 3, "ipfs": 3, "defi": 5, "cryptography": 10,
    # IoT & Robotics
    "mqtt": 3, "aws iot": 5, "bluetooth": 3, "edge computing": 5,
    "ros": 10, "control systems": 10, "sensors": 5, "kinematics": 7,
    "simulation": 5,
    # QA & Testing
    "testing": 5, "test automation": 5, "selenium": 4, "cypress": 3,
    "jest": 3, "pytest": 2, "postman": 2, "performance testing": 4,
    "api testing": 3, "junit": 2, "testng": 2,
    # Mobile
    "react native": 7, "ios": 10, "android": 10, "firebase": 4,
    # Product & Management
    "product management": 7, "agile": 3, "scrum": 3, "user stories": 2,
    "roadmapping": 3, "stakeholder management": 3, "sprint planning": 2,
    "backlog management": 2, "retrospectives": 1, "kanban": 2, "safe": 5,
    "jira": 2, "confluence": 1, "coaching": 5, "team facilitation": 3,
    "project management": 7, "metrics": 3, "a/b testing": 3,
    # Business Analysis
    "business analysis": 7, "requirements gathering": 3, "process modeling": 5,
    "bpmn": 4, "uml": 5, "documentation": 2, "erp systems": 7, "itil": 5,
    "presentation skills": 3,
    # UX/UI Design
    "figma": 4, "user research": 5, "wireframing": 3, "prototyping": 3,
    "design systems": 5, "usability testing": 3, "adobe xd": 3,
    "sketch": 3, "animation": 7, "accessibility": 3,
    # Architecture
    "system design": 14, "microservices": 7, "event driven architecture": 7,
}


def _generate_fallback_roadmap(
    missing_critical: list,
    missing_preferred: list,
    timeline_mode: str,
    timeline_days: Optional[int],
) -> list:
    """Build a roadmap using search-based resource URLs."""
    skills_to_include = list(missing_critical)
    if timeline_mode != "deadline":
        skills_to_include += list(missing_preferred)

    nodes = []
    for i, skill in enumerate(skills_to_include, start=1):
        days = SKILL_LEARNING_DAYS.get(skill.lower(), 3)
        priority = "critical" if skill in missing_critical else "preferred"

        # Scale resources by days
        n_resources = 1 if days <= 1 else (2 if days <= 3 else 3)

        yt_q = quote(skill + " tutorial")
        gfg_q = quote(skill)
        fc_q = quote(skill)
        mdn_q = quote(skill)

        all_videos = [
            {"title": f"{skill.title()} Full Tutorial", "url": f"https://www.youtube.com/results?search_query={yt_q}"},
            {"title": f"{skill.title()} Crash Course", "url": f"https://www.youtube.com/results?search_query={quote(skill + ' crash course')}"},
            {"title": f"{skill.title()} for Beginners", "url": f"https://www.youtube.com/results?search_query={quote(skill + ' for beginners')}"},
        ]
        all_articles = [
            {"title": f"{skill.title()} — GeeksforGeeks", "url": f"https://www.geeksforgeeks.org/search/?gq={gfg_q}"},
            {"title": f"{skill.title()} — freeCodeCamp", "url": f"https://www.freecodecamp.org/news/search/?query={fc_q}"},
            {"title": f"{skill.title()} — MDN / Official Docs", "url": f"https://developer.mozilla.org/en-US/search?q={mdn_q}"},
        ]

        nodes.append({
            "order": i,
            "skill": skill,
            "days_allocated": days,
            "priority": priority,
            "reason": f"{'Core requirement' if priority == 'critical' else 'Nice-to-have'} for the {skill} competency needed in this role.",
            "resources": {
                "videos": all_videos[:n_resources],
                "articles": all_articles[:n_resources],
            },
        })

    return nodes


def run_fallback(
    user_skills: list,
    target_role: str,
    project_descriptions: list,
    timeline_mode: str,
    timeline_days: Optional[int],
) -> dict:
    roles_db, aliases = _load_data()

    if target_role not in roles_db:
        # Unknown role — return a safe minimal response rather than crashing
        return {
            "match_percentage": 0,
            "matching_skills": [],
            "project_derived_skills": [],
            "missing_critical": [],
            "missing_preferred": [],
            "strengths": [],
            "recommendations": [f"Role '{target_role}' not found in database. Try a listed role."],
            "estimated_learning_times": {},
            "roadmap_type": "comprehensive",
            "source": "fallback",
        }

    role = roles_db[target_role]
    user_set = _normalize(user_skills, aliases)
    required_set = set(role["required_skills"])     # already lowercase in JSON
    preferred_set = set(role["preferred_skills"])

    matching = user_set & required_set
    missing_critical = list(required_set - user_set)
    missing_preferred = list(preferred_set - user_set)
    match_pct = round(len(matching) / len(required_set) * 100) if required_set else 0

    # Project-derived skills: simple keyword scan of descriptions
    project_text = " ".join(project_descriptions).lower()
    project_derived = []
    for skill in required_set | preferred_set:
        if skill in project_text and skill not in user_set:
            project_derived.append(skill)

    # Build estimated learning times for missing critical skills
    estimated_times = {
        s: f"{SKILL_LEARNING_DAYS.get(s, '?')} days"
        for s in missing_critical
    }

    roadmap_type = "comprehensive"
    if timeline_mode == "deadline" and timeline_days:
        roadmap_type = "accelerated"
        buffer = timeline_days * 0.8
        learnable = [s for s in missing_critical if SKILL_LEARNING_DAYS.get(s, 999) <= buffer]
        recommendations = [f"Learn {s.title()} ({SKILL_LEARNING_DAYS.get(s,'?')} days)" for s in learnable[:3]]
        if not recommendations:
            recommendations = ["Your deadline is very tight — focus on reviewing existing skills first."]
    else:
        recommendations = [f"Learn {s.title()}" for s in missing_critical[:3]]

    roadmap = _generate_fallback_roadmap(
        missing_critical, missing_preferred, timeline_mode, timeline_days
    )

    return {
        "match_percentage": match_pct,
        "matching_skills": sorted(matching),
        "project_derived_skills": project_derived,
        "missing_critical": missing_critical,
        "missing_preferred": missing_preferred,
        "strengths": sorted(matching),
        "recommendations": recommendations,
        "estimated_learning_times": estimated_times,
        "roadmap_type": roadmap_type,
        "roadmap": roadmap,
        "source": "fallback",
    }
