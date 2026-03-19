"""
Gemini API integration for skill gap analysis and roadmap generation.
"""

import os
import json
import re
from typing import Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote
import httpx
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

REQUIRED_FIELDS = {
    "match_percentage",
    "matching_skills",
    "project_derived_skills",
    "missing_critical",
    "missing_preferred",
    "strengths",
    "recommendations",
    "estimated_learning_times",
    "roadmap_type",
}

GEMINI_TIMEOUT_SECONDS = 60
GEMINI_MODELS = ["gemini-3.1-flash-lite-preview", "gemini-3-flash-preview"]


def _extract_json(raw_text: str) -> Optional[dict]:
    """Try multiple strategies to parse JSON from Gemini's response."""
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        pass

    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n", 1)
        cleaned = lines[1] if len(lines) > 1 else ""
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r'\{.*\}', raw_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None


def _validate_response(data: dict) -> bool:
    """Check all required fields are present and non-null."""
    return all(field in data and data[field] is not None for field in REQUIRED_FIELDS)


def _call_model_with_prompt(prompt: str) -> Optional[dict]:
    """
    Try each model in GEMINI_MODELS in order.
    Returns first successfully parsed dict, or None if all models fail.
    Moves to next model on rate limit errors.
    """
    for model_name in GEMINI_MODELS:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=4096,
                ),
                request_options={"timeout": GEMINI_TIMEOUT_SECONDS},
            )
            data = _extract_json(response.text.strip())
            if data:
                print(f"[DEBUG] {model_name} succeeded")
                return data
            print(f"[DEBUG] Could not parse JSON from {model_name}")

        except Exception as e:
            error_str = str(e)
            is_rate_limit = (
                "429" in error_str
                or "RESOURCE_EXHAUSTED" in error_str
                or "rate" in error_str.lower()
            )
            if is_rate_limit:
                print(f"[DEBUG] Rate limit on {model_name}, trying next model...")
            else:
                print(f"[DEBUG] Error with {model_name}: {type(e).__name__}: {error_str}")

    print("[DEBUG] All models exhausted")
    return None


def _build_analysis_prompt(
    skills: List[str],
    experience_level: str,
    target_role: str,
    project_descriptions: List[str],
    timeline_mode: str,
    timeline_days: Optional[int],
) -> str:
    projects_text = (
        "\n".join(f"  - {d}" for d in project_descriptions)
        if project_descriptions else "  - (none provided)"
    )
    timeline_instruction = (
        f"The candidate has {timeline_days} days to prepare. "
        f"Prioritize skills that are high-impact AND learnable within this timeframe. "
        f"Set roadmap_type to 'accelerated'."
        if timeline_mode == "deadline" and timeline_days
        else "There is no time constraint. Provide a comprehensive learning roadmap. Set roadmap_type to 'comprehensive'."
    )

    return f"""You are a career skills gap analyst. Analyze the following candidate profile and return a structured JSON response.

Candidate profile:
- Listed skills: {skills}
- Experience level: {experience_level}
- Target role: {target_role}
- Past projects (for context only — extract implicit skills from these):
{projects_text}
- Learning timeline: {timeline_instruction}

Instructions:
1. Identify skills the candidate already has that match the target role (matching_skills).
2. Extract implicit skills from the project descriptions that the candidate didn't explicitly list (project_derived_skills).
3. Identify critical missing skills (missing_critical) and nice-to-have missing skills (missing_preferred).
4. Generate top 3 recommendations ordered by impact and learnability within the timeline.
5. Estimate days to working competency for each missing critical skill (estimated_learning_times).

Return ONLY a valid JSON object with exactly these keys (no extra text, no markdown):
{{
  "match_percentage": <integer 0-100>,
  "matching_skills": ["skill1", "skill2"],
  "project_derived_skills": ["skill1", "skill2"],
  "missing_critical": ["skill1", "skill2"],
  "missing_preferred": ["skill1", "skill2"],
  "strengths": ["brief strength 1", "brief strength 2"],
  "recommendations": ["Actionable step 1", "Actionable step 2", "Actionable step 3"],
  "estimated_learning_times": {{"skill": "X days"}},
  "roadmap_type": "accelerated" or "comprehensive"
}}"""


def call_gemini(
    skills: List[str],
    experience_level: str,
    target_role: str,
    project_descriptions: List[str],
    timeline_mode: str,
    timeline_days: Optional[int],
) -> Optional[dict]:
    """
    Run the main gap analysis via Gemini. Returns parsed dict or None on failure.
    None signals the caller to use the rule-based fallback.
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    force_fallback = os.getenv("FORCE_FALLBACK", "false").lower() == "true"

    if force_fallback or not api_key or api_key == "your_gemini_api_key_here":
        print(f"[DEBUG] Skipping Gemini (force_fallback={force_fallback}, no_key={not api_key})")
        return None

    genai.configure(api_key=api_key)

    data = _call_model_with_prompt(
        _build_analysis_prompt(
            skills, experience_level, target_role,
            project_descriptions, timeline_mode, timeline_days
        )
    )

    if data is None or not _validate_response(data):
        print("[DEBUG] Main analysis failed or incomplete")
        return None

    data["source"] = "gemini"
    print("[DEBUG] Main analysis succeeded!")
    return data


# Prompt 1 — Node Planner
def _build_nodes_prompt(
    target_role: str,
    experience_level: str,
    missing_critical: List[str],
    missing_preferred: List[str],
    timeline_mode: str,
    timeline_days: Optional[int],
) -> str:
    if timeline_mode == "deadline" and timeline_days:
        timeline_text = (
            f"The candidate has {timeline_days} days to prepare. "
            f"Total days across ALL nodes MUST NOT exceed {timeline_days}. "
            f"Focus only on the most critical skills. Prioritize by role impact."
        )
    else:
        timeline_text = (
            "No time constraint. Include all skills — critical ones first, preferred ones after. "
            "Be comprehensive."
        )

    return f"""You are a career learning roadmap architect.

Candidate gap analysis:
- Target role: {target_role}
- Experience level: {experience_level}
- Missing critical skills: {missing_critical}
- Missing preferred skills: {missing_preferred}
- Timeline: {timeline_text}

Create an ordered list of skill nodes to learn. Rules:
1. Deadline mode: total days must not exceed {timeline_days if timeline_days else "N/A"}, critical skills only.
2. Relaxed mode: include all skills, critical first then preferred.
3. Day estimates — very simple: 1 day, simple: 2-3 days, intermediate: 5-7 days, advanced: 10-14 days.

Return ONLY valid JSON (no markdown, no extra text):
{{
  "roadmap_nodes": [
    {{
      "order": 1,
      "skill": "skill name",
      "days_allocated": <integer>,
      "priority": "critical" or "preferred",
      "reason": "one sentence explaining why this skill matters for {target_role}"
    }}
  ],
  "total_days": <integer>
}}"""


# Prompt 2 — Prerequisite Linker
def _build_linker_prompt(nodes: List[dict]) -> str:
    nodes_json = json.dumps(nodes, indent=2)
    skill_names = [n["skill"] for n in nodes]

    return f"""You are a learning path architect for software developers.

Below are skill nodes for a learning roadmap. Your ONLY job is to define prerequisite relationships to form a BRANCHING dependency graph — like the NeetCode roadmap, NOT a straight chain.

Nodes:
{nodes_json}

Available skill names (use these exactly): {skill_names}

RULES — follow ALL of these strictly:

1. CONNECTED GRAPH: No stranded or isolated nodes. Every node must be a root or reachable from a root.

2. BRANCHING REQUIRED — most important rule:
   - A pure linear chain (A→B→C→D→E...) is FORBIDDEN unless there are 3 or fewer total nodes.
   - Root nodes MUST have at least 2 children where possible.
   - Create PARALLEL tracks for skills that are genuinely independent of each other.
     Good example: "Pandas" and "NumPy" can BOTH follow "Python" as siblings — not chained.
     Good example: "Docker" and "SQL" can BOTH follow "Linux" as siblings — not chained.
   - Aim for at least {max(2, len(nodes) // 3)} nodes at the same depth level.

3. DEPTH LIMIT: No single chain longer than 3 levels deep (root → L1 → L2 → L3 max) without strong reason.

4. SINGLE ROOT preferred: 1-2 root nodes (empty prerequisites []) for a clean entry point.

5. HIERARCHY: Every non-root node needs at least one prerequisite based on genuine learning order.

6. VALID NAMES ONLY: Prerequisites must use names EXACTLY as listed above.

7. NO CYCLES: A cannot require B if B already requires A (directly or indirectly).

Return the SAME nodes with prerequisites filled in. Return ONLY valid JSON (no markdown, no extra text):
{{
  "roadmap_nodes": [
    {{
      "order": <integer>,
      "skill": "exact skill name",
      "days_allocated": <integer>,
      "priority": "critical" or "preferred",
      "reason": "same reason as input",
      "prerequisites": ["skill that must be learned first"]
    }}
  ]
}}"""


# Prompt 3 — Resource Generator
def _build_resources_prompt(nodes: List[dict]) -> str:
    nodes_json = json.dumps(nodes, indent=2)

    return f"""You are a learning resource curator for software developers.

For each skill node below, find specific learning resources. Scale the number based on days_allocated:
- 1 day → 1 YouTube video + 1 article
- 2 to 3 days → 2 YouTube videos + 2 articles
- 4 or more days → 3 YouTube videos + 3 articles

Roadmap nodes:
{nodes_json}

CRITICAL RULES:

1. SPECIFICITY: Every resource must be directly and exclusively about the exact skill in the node.
   - "Scikit-Learn" node → Scikit-Learn tutorial, NOT a general Machine Learning overview.
   - "Docker" node → Docker tutorial, NOT a general DevOps overview.
   - Use the "reason" field for context on what angle to focus on.

2. NO GENERIC CONTENT: Do NOT link broad topic overviews.
   - BAD: "Machine Learning Full Course" for a Scikit-Learn node.
   - GOOD: "Scikit-Learn Tutorial for Beginners" for a Scikit-Learn node.

3. YOUTUBE: Real, specific video URLs from known educators — freeCodeCamp, Fireship, Traversy Media, TechWorld with Nana, Academind, NetworkChuck, Corey Schafer, Sentdex.
   - Format: https://www.youtube.com/watch?v=VIDEO_ID

4. ARTICLES: Stable, reliable sources only — in order of preference: official docs (pytorch.org, docs.python.org, developer.mozilla.org, kubernetes.io, etc.), GeeksforGeeks, Real Python, DigitalOcean, W3Schools, AWS/GCP/Azure docs, Towards Data Science.
   - AVOID freeCodeCamp.org for articles — their URLs frequently go dead.
   - URL must link directly to a specific article or tutorial page, not a homepage.

Return ONLY valid JSON (no markdown, no extra text):
{{
  "roadmap": [
    {{
      "order": <integer>,
      "skill": "skill name",
      "days_allocated": <integer>,
      "priority": "critical" or "preferred",
      "reason": "one sentence",
      "prerequisites": ["..."],
      "resources": {{
        "videos": [{{"title": "...", "url": "https://www.youtube.com/watch?v=..."}}],
        "articles": [{{"title": "...", "url": "https://..."}}]
      }}
    }}
  ]
}}"""


def _check_youtube_url(url: str) -> bool:
    """Validate YouTube URL via oEmbed. Returns True if video exists and is public."""
    try:
        oembed = f"https://www.youtube.com/oembed?url={url}&format=json"
        r = httpx.get(oembed, timeout=5, follow_redirects=True)
        return r.status_code == 200
    except Exception:
        return False


def _check_article_url(url: str) -> bool:
    """
    Validate an article URL. Uses GET with redirect tracking to catch soft 404s.

    Soft 404 detection covers three cases:
    - Redirect to homepage: final URL path is root after following redirects (freeCodeCamp, Medium)
    - freeCodeCamp: /news/ path disappears after redirect
    - GeeksforGeeks: returns HTTP 200 but HTML title contains "| 404"
    """
    try:
        from urllib.parse import urlparse
        r = httpx.get(url, timeout=8, follow_redirects=True)
        if r.status_code >= 400:
            return False

        # Soft 404 detection: check if we were redirected to a much shorter path
        original_path = urlparse(url).path.rstrip("/")
        final_path = urlparse(str(r.url)).path.rstrip("/")

        # If original had a real article path but final is root or much shorter, it's dead
        if len(original_path) > 10 and len(final_path) <= 1:
            print(f"[DEBUG] Soft 404 detected: {url} → {r.url}")
            return False

        # freeCodeCamp-specific: article paths start with /news/ — if final URL lost that, it's gone
        if "freecodecamp.org/news/" in url and "/news/" not in final_path:
            print(f"[DEBUG] freeCodeCamp soft 404: {url} → {r.url}")
            return False

        # GeeksforGeeks-specific: GFG returns HTTP 200 for deleted pages but the
        # HTML title contains "| 404" — check the response body title tag
        if "geeksforgeeks.org" in url:
            import re
            title_match = re.search(r"<title[^>]*>(.*?)</title>", r.text, re.IGNORECASE | re.DOTALL)
            if title_match and "404" in title_match.group(1):
                print(f"[DEBUG] GFG soft 404 (title contains 404): {url}")
                return False

        return True
    except Exception:
        return False


def _collect_and_validate_urls(roadmap: List[dict]) -> Tuple[dict, List[dict]]:
    """
    Validate all video and article URLs in parallel.
    Returns:
      - results dict: {(ni, "video"|"article", vi): bool}
      - dead_links list: [{skill, type, dead_url, title}] for repair prompt
    """
    checks = []  # (ni, kind, vi, url)
    for ni, node in enumerate(roadmap):
        for vi, v in enumerate(node.get("resources", {}).get("videos", [])):
            checks.append((ni, "video", vi, v["url"]))
        for ai, a in enumerate(node.get("resources", {}).get("articles", [])):
            checks.append((ni, "article", ai, a["url"]))

    if not checks:
        return {}, []

    print(f"[DEBUG] Validating {len(checks)} URLs in parallel ({sum(1 for c in checks if c[1]=='video')} videos, {sum(1 for c in checks if c[1]=='article')} articles)...")
    results = {}
    with ThreadPoolExecutor(max_workers=12) as executor:
        future_map = {}
        for ni, kind, idx, url in checks:
            fn = _check_youtube_url if kind == "video" else _check_article_url
            future_map[executor.submit(fn, url)] = (ni, kind, idx, url)

        for future in as_completed(future_map):
            ni, kind, idx, url = future_map[future]
            results[(ni, kind, idx)] = future.result()

    # Collect dead links with context for the repair prompt
    dead_links = []
    for ni, kind, idx, url in checks:
        if not results.get((ni, kind, idx), True):
            node = roadmap[ni]
            resources = node.get("resources", {})
            items = resources.get("videos" if kind == "video" else "articles", [])
            title = items[idx]["title"] if idx < len(items) else ""
            dead_links.append({
                "skill": node.get("skill", ""),
                "type": kind,
                "dead_url": url,
                "title": title,
            })

    print(f"[DEBUG] Validation done: {len(dead_links)} dead links found")
    return results, dead_links


def _build_repair_prompt(dead_links: List[dict]) -> str:
    dead_json = json.dumps(dead_links, indent=2)

    return f"""You are a learning resource curator for software developers.

The following learning resource URLs have been validated and are no longer accessible (404, deleted, private, or moved). For each dead URL, provide ONE valid replacement.

Dead links:
{dead_json}

RULES:
1. Each replacement must be a real, currently live URL.
2. For type "video": YouTube URL only. Format: https://www.youtube.com/watch?v=VIDEO_ID. Preferred channels: Traversy Media, Fireship, TechWorld with Nana, Academind, Corey Schafer, Sentdex, NetworkChuck, Programming with Mosh.
3. For type "article": PREFER stable official documentation or GeeksforGeeks over freeCodeCamp (freeCodeCamp articles frequently get deleted). Best sources in order of preference: official docs (pytorch.org, docs.python.org, developer.mozilla.org, etc.), GeeksforGeeks, Real Python, DigitalOcean, W3Schools. Must link to a specific page, not a homepage.
4. The replacement MUST cover the same skill as the dead link (see "skill" field).
5. Do NOT reuse the dead_url as the replacement.
6. Do NOT generate URLs you are not certain exist. 

AGAIN MAKE SURE EACH ARTICLE LINK OR VIDEO LINK GENERATED NEITHER RETURNS A 404 ERROR NOR CONTAINS ZERO CONTENT ON THE SKILL. 

Return ONLY valid JSON (no markdown, no extra text):
{{
  "replacements": [
    {{
      "dead_url": "exact dead URL from input",
      "title": "title for the replacement resource",
      "url": "new valid URL"
    }}
  ]
}}"""


def _apply_repairs(roadmap: List[dict], dead_links: List[dict]) -> List[dict]:
    """
    Send dead links to Gemini for replacement URLs, validate those replacements,
    then apply only the ones that actually work. Anything still dead falls back
    to a guaranteed YouTube/GFG search URL.
    """
    if not dead_links:
        return roadmap

    print(f"[DEBUG] Sending {len(dead_links)} dead links to repair prompt...")
    repair_result = _call_model_with_prompt(_build_repair_prompt(dead_links))

    # Build raw repair map: dead_url → {title, url}
    raw_repair_map = {}
    if repair_result and repair_result.get("replacements"):
        for r in repair_result["replacements"]:
            if r.get("dead_url") and r.get("url") and r["url"] != r["dead_url"]:
                raw_repair_map[r["dead_url"]] = {"title": r.get("title", ""), "url": r["url"]}
        print(f"[DEBUG] Repair prompt returned {len(raw_repair_map)} candidate replacements")
    else:
        print("[DEBUG] Repair prompt failed — will use search fallbacks for all dead links")

    # Validate each replacement URL before accepting it
    repair_map = {}
    if raw_repair_map:
        dead_link_types = {d["dead_url"]: d["type"] for d in dead_links}
        print(f"[DEBUG] Validating {len(raw_repair_map)} repair candidates...")
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_map = {}
            for dead_url, replacement in raw_repair_map.items():
                kind = dead_link_types.get(dead_url, "article")
                fn = _check_youtube_url if kind == "video" else _check_article_url
                future_map[executor.submit(fn, replacement["url"])] = (dead_url, replacement)
            for future in as_completed(future_map):
                dead_url, replacement = future_map[future]
                if future.result():
                    repair_map[dead_url] = replacement
                    print(f"[DEBUG] Repair validated: {replacement['url']}")
                else:
                    print(f"[DEBUG] Repair also dead, will use search fallback: {replacement['url']}")

    print(f"[DEBUG] {len(repair_map)}/{len(dead_links)} repaired with live URLs, rest → search fallback")

    # Apply validated repairs to roadmap
    for node in roadmap:
        skill = node.get("skill", "")
        yt_search = f"https://www.youtube.com/results?search_query={quote(skill + ' tutorial')}"
        gfg_search = f"https://www.geeksforgeeks.org/search/?gq={quote(skill)}"

        for video in node.get("resources", {}).get("videos", []):
            if video["url"] in repair_map:
                replacement = repair_map[video["url"]]
                print(f"[DEBUG] Repaired video for '{skill}': {video['url']} → {replacement['url']}")
                video["title"] = replacement["title"]
                video["url"] = replacement["url"]

        for article in node.get("resources", {}).get("articles", []):
            if article["url"] in repair_map:
                replacement = repair_map[article["url"]]
                print(f"[DEBUG] Repaired article for '{skill}': {article['url']} → {replacement['url']}")
                article["title"] = replacement["title"]
                article["url"] = replacement["url"]

    # Final pass: replace any still-dead links with search fallbacks
    dead_url_set = {d["dead_url"] for d in dead_links}
    repaired_url_set = set(repair_map.keys())
    still_dead = dead_url_set - repaired_url_set

    for node in roadmap:
        skill = node.get("skill", "")
        yt_search = f"https://www.youtube.com/results?search_query={quote(skill + ' tutorial')}"
        gfg_search = f"https://www.geeksforgeeks.org/search/?gq={quote(skill)}"

        for video in node.get("resources", {}).get("videos", []):
            if video["url"] in still_dead:
                video["title"] = f"{skill} Tutorial — YouTube Search"
                video["url"] = yt_search

        for article in node.get("resources", {}).get("articles", []):
            if article["url"] in still_dead:
                article["title"] = f"{skill} — GeeksforGeeks Search"
                article["url"] = gfg_search

    return roadmap


def _deduplicate_resources(roadmap: List[dict]) -> List[dict]:
    """Remove duplicate URLs within each node's videos and articles."""
    for node in roadmap:
        for key in ("videos", "articles"):
            items = node.get("resources", {}).get(key, [])
            seen = set()
            deduped = []
            for item in items:
                if item["url"] not in seen:
                    seen.add(item["url"])
                    deduped.append(item)
            node["resources"][key] = deduped
    return roadmap


def build_roadmap(
    target_role: str,
    experience_level: str,
    missing_critical: List[str],
    missing_preferred: List[str],
    timeline_mode: str,
    timeline_days: Optional[int],
) -> List[dict]:
    """Build a learning roadmap for the given skill gaps using a 3-prompt chain."""
    if not missing_critical and not missing_preferred:
        return []

    # Prompt 1: Node Planner
    print("[DEBUG] Roadmap — Prompt 1: Node planning")
    nodes_result = _call_model_with_prompt(
        _build_nodes_prompt(
            target_role, experience_level,
            missing_critical, missing_preferred,
            timeline_mode, timeline_days
        )
    )

    if not nodes_result or not nodes_result.get("roadmap_nodes"):
        print("[DEBUG] Prompt 1 failed — no nodes returned")
        return []

    nodes = nodes_result["roadmap_nodes"]
    print(f"[DEBUG] Prompt 1 done: {len(nodes)} nodes, {nodes_result.get('total_days')} total days")

    # Prompt 2: Prerequisite Linker
    print("[DEBUG] Roadmap — Prompt 2: Prerequisite linking")
    linked_result = _call_model_with_prompt(_build_linker_prompt(nodes))

    if linked_result and linked_result.get("roadmap_nodes"):
        nodes = linked_result["roadmap_nodes"]
        print(f"[DEBUG] Prompt 2 done: prerequisites linked for {len(nodes)} nodes")
    else:
        print("[DEBUG] Prompt 2 failed — continuing without prerequisites")

    # Prompt 3: Resource Generator
    print("[DEBUG] Roadmap — Prompt 3: Resource generation")
    resources_result = _call_model_with_prompt(_build_resources_prompt(nodes))

    if not resources_result or not resources_result.get("roadmap"):
        print("[DEBUG] Prompt 3 failed — returning nodes without resources")
        return [{**n, "resources": {"videos": [], "articles": []}} for n in nodes]

    roadmap = resources_result["roadmap"]
    print(f"[DEBUG] Prompt 3 done: {len(roadmap)} nodes enriched with resources")

    # Validate all URLs in parallel
    _, dead_links = _collect_and_validate_urls(roadmap)

    # Repair dead links via Gemini, fall back to search URLs for anything left
    roadmap = _apply_repairs(roadmap, dead_links)

    # Deduplicate resources
    roadmap = _deduplicate_resources(roadmap)

    return roadmap
