from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from services.gemini_service import call_gemini, build_roadmap
from services.fallback_service import run_fallback

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze/{profile_id}", response_model=schemas.AnalysisOut)
def analyze_profile(profile_id: int, db: Session = Depends(get_db)):
    """Run gap analysis for a profile. Tries Gemini first, falls back to rule-based analysis."""
    profile = db.query(models.Profile).filter(models.Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found.")

    project_descriptions = [p.description for p in profile.projects]

    result = call_gemini(
        skills=profile.skills,
        experience_level=profile.experience_level,
        target_role=profile.target_role,
        project_descriptions=project_descriptions,
        timeline_mode=profile.timeline_mode,
        timeline_days=profile.timeline_days,
    )

    if result is None:
        result = run_fallback(
            user_skills=profile.skills,
            target_role=profile.target_role,
            project_descriptions=project_descriptions,
            timeline_mode=profile.timeline_mode,
            timeline_days=profile.timeline_days,
        )
    else:
        result["roadmap"] = build_roadmap(
            target_role=profile.target_role,
            experience_level=profile.experience_level,
            missing_critical=result.get("missing_critical", []),
            missing_preferred=result.get("missing_preferred", []),
            timeline_mode=profile.timeline_mode,
            timeline_days=profile.timeline_days,
        )

    existing = db.query(models.AnalysisResult).filter(
        models.AnalysisResult.profile_id == profile_id
    ).first()

    if existing:
        for key, value in result.items():
            if hasattr(existing, key):
                setattr(existing, key, value)
        analysis_row = existing
    else:
        analysis_row = models.AnalysisResult(profile_id=profile_id, **result)
        db.add(analysis_row)

    db.commit()
    db.refresh(analysis_row)
    return analysis_row


@router.get("/analyze/{profile_id}", response_model=schemas.AnalysisOut)
def get_analysis(profile_id: int, db: Session = Depends(get_db)):
    """
    Retrieve the saved analysis for a profile without re-running it.
    Returns 404 if no analysis has been run yet.
    """
    profile = db.query(models.Profile).filter(models.Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found.")

    if not profile.analysis:
        raise HTTPException(
            status_code=404,
            detail="No analysis found for this profile. Run POST /api/analyze/{id} first."
        )
    return profile.analysis


@router.get("/roles", tags=["roles"])
def list_roles(search: str = ""):
    """Return available target roles, optionally filtered by search term."""
    import json
    from pathlib import Path

    data_path = Path(__file__).resolve().parent.parent.parent / "data" / "job_roles.json"
    with open(data_path) as f:
        roles = json.load(f)

    if search:
        term = search.lower()
        roles = {k: v for k, v in roles.items() if term in k.lower() or term in v["category"].lower()}

    return [{"role": k, "category": v["category"]} for k, v in roles.items()]
