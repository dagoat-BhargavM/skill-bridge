# Skill-Bridge — Career Navigator

**Candidate Name:** Bhargav V Mukhami | 
**Scenario Chosen:** 2 — Skill-Bridge Career Navigator | 
**Estimated Time Spent:** ~5 hours

---

## Video

🎥 [Link to screen recording — Vimeo]: https://vimeo.com/1175417238/cce4f0f97e?share=copy&fl=sv&fe=ci

---

## Problem

Students and early-career professionals face a "skills gap" — they know what role they want, but they don't know exactly what's missing or where to focus first. Job descriptions list 15+ requirements, certification sites are overwhelming, and there's no single tool that says: "Here's where you are, here's the gap, and here's your fastest path forward."

Skill-Bridge solves this by taking a user's skills, past project experience, and available prep time — and generating a personalized, prioritized learning roadmap.

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- A Google Gemini API key 

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Add your GEMINI_API_KEY
uvicorn main:app --reload
```

API docs available at: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App runs at: http://localhost:5173

### Run Tests

```bash
cd backend
pytest tests/ -v
```

---

## Architecture

```
Frontend (React + Vite + Tailwind)
    ↓ axios calls
Backend (FastAPI + SQLAlchemy)
    ├── /api/profiles     → Profile CRUD
    ├── /api/analyze/{id} → Gap analysis (Gemini → fallback)
    └── /api/roles        → Role list + search
    ↓
SQLite (persistent storage)
    ↓
Gemini API → Rule-based fallback
```

---

## AI Integration & Fallback

The `/analyze` endpoint uses **Google Gemini** (gemini-3.1-flash-lite-preview) to:
1. Analyze the user's listed skills vs. target role requirements
2. Extract implicit skills from project descriptions (e.g., "deployed on AWS" → AWS competency)
3. Generate prioritized recommendations based on timeline (accelerated vs. comprehensive)

**Fallback triggers (any one of):**
- Gemini API error or network timeout
- Response is not valid JSON
- Parsed JSON is missing any required field *(Decision: strict validation — partial data is not trusted)*

The fallback uses a local `job_roles.json` taxonomy with rule-based keyword matching and timeline-aware skill filtering.

**Transparency:** Every analysis result includes a `source` field (`"gemini"` or `"fallback"`) displayed in the UI so the user always knows which path was used.

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Fallback trigger | Any missing required field (1C) | Partial AI output is worse than clean rule-based output — the UI needs a complete contract |
| Analysis persistence | Save to DB (not recompute) | Non-deterministic re-generation is bad UX — users track progress against a fixed roadmap |
| Skill normalization | Lowercase only | Simple, predictable, covers real input variance without brittle alias chains |
| Projects | Descriptions only | Projects are portfolio context for skill inference — deadline is a separate concern |
| Learning timeline | Separate from projects | Decouples "what you've built" from "when you need to be ready" |
| Database | SQLite | Zero setup, sufficient for prototype; swap to PostgreSQL for production |

---

## AI Disclosure

- **Did you use an AI assistant?** Yes — used Claude (Anthropic) for scaffolding, syntax checking, and prompt engineering guidance.
- **How did you verify suggestions?** Reviewed all generated code for correctness, tested edge cases manually, and validated architectural decisions against requirements.
- **Examples of rejected/changed suggestions:**
  - Used a React graph library (React Flow) for the DAG roadmap — rejected in favour of a custom SVG + HTML hybrid renderer to avoid the dependency and show understanding of layout primitives (Kahn's BFS topological sort).
  - Initial dead link handling replaced bad URLs immediately with YouTube search fallbacks — changed to send them back to Gemini for a real replacement first, with search as a last resort only.
  - Single combined prompt for node planning + prerequisite linking — split into two separate prompts after the combined version consistently produced stranded nodes with no connections.

---

## Tradeoffs & What's Next

**What I cut for scope:**
- Resume/PDF upload (would add PDF parser complexity, manual input is more reliable for a prototype)
- User authentication
- Cloud deployment 

**What I'd build next:**
- Document-based input: accept a candidate's resume and a job description as uploaded documents (PDF/DOCX), parse both, and run the same gap analysis pipeline automatically — eliminating manual skill entry entirely
- Multi-role comparison: compare gap against 2-3 roles simultaneously
- Progress tracking: mark skills as learned over time, watch match % grow
- Collaborative mode: mentor can view mentee's roadmap and annotate recommendations

**Known limitations:**
- Skills taxonomy covers 35 roles across 9 categories (Software Engineering, Cloud, Data, AI/ML, Cybersecurity, QA, Emerging Tech, Product, Design); niche or emerging skills may not match
- Gemini free tier has rate limits — fallback ensures the app still works
- No auth means profiles are not user-scoped

---

## Synthetic Data

Sample profiles, job roles, and skills taxonomy are in `/data/`.
