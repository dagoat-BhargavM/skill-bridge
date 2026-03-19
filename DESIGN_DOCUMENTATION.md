# Skill-Bridge — Design Documentation

**Candidate:** Bhargav V Mukhami | 
**Scenario:** 2 — Skill-Bridge Career Navigator

---

## Problem

Students and early-career professionals know the role they want but not the exact gap between where they are and where they need to be. Job descriptions are long, learning resources are scattered, and there's no tool that gives a single, prioritised answer: *here's what you're missing, here's how long it'll take, and here's where to start.*

---

## Solution Overview

Skill-Bridge takes a user's current skills, past project experience, and available prep time, and outputs a personalised gap analysis with an interactive learning roadmap. The roadmap is structured as a dependency graph (similar to NeetCode's roadmap) so users see not just *what* to learn but *in what order* and *why*.

---

## System Design

```
User (Browser)
    │
    ▼
React + Vite + Tailwind (port 5173)
    │  Axios → /api/*  (Vite proxy forwards to port 8000)
    ▼
FastAPI + SQLAlchemy (port 8000)
    ├── POST /api/profiles         → create profile
    ├── PUT  /api/profiles/{id}    → update profile
    ├── DEL  /api/profiles/{id}    → delete profile
    ├── GET  /api/roles            → list 35 target roles
    └── POST /api/analyze/{id}     → gap analysis + roadmap
              │
              ├── Primary: Gemini API (3-prompt chain)
              │     Prompt 1 — Node Planner
              │     Prompt 2 — Prerequisite Linker (DAG)
              │     Prompt 3 — Resource Generator
              │     + URL validation + repair loop
              │
              └── Fallback: rule-based (job_roles.json taxonomy)
                    guaranteed to always return a complete result
    │
    ▼
SQLite (persisted analysis results — users revisit without re-running)
```

### AI Pipeline — 3-Prompt Chain of Thought

Rather than sending one large prompt, the roadmap is generated in three focused sequential steps:

**Prompt 1 — Node Planner:** Receives the skill gaps and timeline. Returns an ordered list of skill nodes with day allocations. Does not set prerequisites — keeps this prompt's scope narrow.

**Prompt 2 — Prerequisite Linker:** Receives the nodes from Prompt 1. Its only job is to set prerequisite relationships and produce a connected DAG with no isolated nodes. Enforces branching (parallel tracks where skills are independent) and a max depth of 3 levels.

**Prompt 3 — Resource Generator:** Receives the linked nodes. Returns each node enriched with specific YouTube videos and articles from trusted sources (official docs, GeeksforGeeks, Real Python, etc.).

### URL Validation & Repair Loop

After Prompt 3, all URLs (videos and articles) are validated in parallel using `ThreadPoolExecutor`. YouTube links are checked via the oEmbed API. Article links use a GET request with soft-404 detection (redirect path comparison) to catch sites like freeCodeCamp that return HTTP 200 for deleted pages.

Dead links are batched and sent to a repair prompt asking Gemini for live replacements. Repair candidates are validated before being applied. Anything that still fails falls back to a YouTube search URL or GeeksforGeeks search URL — guaranteed to always resolve.

### Fallback Strategy

If Gemini is unavailable, rate-limited, returns unparseable JSON, or returns incomplete data, the system falls back to a rule-based engine. The fallback uses `job_roles.json` for skill matching and produces a roadmap using YouTube/GFG search URLs that always work. The UI shows a "Rule-based fallback" badge so the user always knows which path was used.

---

## Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| Frontend | React + Vite + Tailwind CSS | Fast dev, utility-first styling, no config overhead |
| Routing | React Router v6 | Client-side navigation without page reloads |
| HTTP client | Axios | Clean API wrapper; Vite proxy removes CORS complexity |
| Backend | FastAPI (Python) | Auto-generated docs at `/docs`, async-ready, Pydantic validation |
| ORM | SQLAlchemy + SQLite | Zero-setup persistence; swap to PostgreSQL for production |
| AI | Google Gemini API (`gemini-3.1-flash-lite-preview`) | Free tier, reliable JSON output, fast response |
| HTTP validation | httpx | Per-request timeouts, redirect tracking for soft-404 detection |
| Concurrency | `ThreadPoolExecutor` | Parallel URL validation — ~20 checks complete in ~2s instead of ~20s |
| Testing | pytest | 16 tests covering profile CRUD and analysis/fallback paths |

---

## Key Design Decisions

**Strict fallback trigger:** Fallback activates on any missing required field, not just total API failure. Partial AI output with missing fields is worse than a complete rule-based result.

**3-prompt chain over 1 large prompt:** A single combined prompt produced stranded nodes and prerequisite name mismatches. Splitting into Node Planner → Prerequisite Linker → Resource Generator gave each step a narrow, reliable scope.

**Custom DAG renderer over React Flow:** Avoided the dependency in favour of a custom hybrid SVG + HTML renderer using Kahn's BFS topological sort — the same approach NeetCode uses. SVG layer draws bezier edges; HTML div layer renders clickable Tailwind cards.

**Repair prompt before search fallback:** Replacing dead links immediately with search URLs is reliable but low quality. Sending dead links back to Gemini for a validated replacement first keeps >80% of links as direct, specific resources.

**Analysis persistence:** Results are saved to the database so users can return to their roadmap without triggering a new API call. Re-running analysis only happens when the user explicitly requests it or edits their profile.

---

## Future Enhancements

**Document-based input:** Accept a candidate's resume (PDF/DOCX) and a job description as uploaded files — parse both and run the same pipeline automatically, eliminating manual skill entry entirely.

**Multi-role comparison:** Run gap analysis against 2–3 target roles simultaneously and display a side-by-side view so users can choose their highest-match path.

**Progress tracking:** Let users mark skills as learned over time and watch their match percentage grow as they complete roadmap nodes.

**Collaborative mode:** Allow a mentor to view a mentee's roadmap, annotate specific nodes with advice, and track the mentee's progress over time.

**Cloud deployment:** Containerise the backend with Docker, serve the frontend via a CDN, and add JWT authentication so profiles are user-scoped in a production environment.
