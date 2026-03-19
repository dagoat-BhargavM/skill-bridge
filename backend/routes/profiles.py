from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
import models
import schemas

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


@router.post("/", response_model=schemas.ProfileOut, status_code=201)
def create_profile(payload: schemas.ProfileCreate, db: Session = Depends(get_db)):
    """Create a new profile with skills, projects, and learning timeline."""
    profile = models.Profile(
        name=payload.name,
        skills=payload.skills,
        experience_level=payload.experience_level,
        target_role=payload.target_role,
        timeline_mode=payload.timeline_mode,
        timeline_days=payload.timeline_days,
    )
    db.add(profile)
    db.flush()  # get profile.id before adding children

    for proj in payload.projects:
        db.add(models.Project(profile_id=profile.id, description=proj.description))

    db.commit()
    db.refresh(profile)
    return profile


@router.get("/", response_model=list[schemas.ProfileOut])
def list_profiles(
    search: Optional[str] = Query(None, description="Search profiles by name or target role"),
    role: Optional[str] = Query(None, description="Filter by exact target role"),
    db: Session = Depends(get_db)
):
    """List all profiles. Optionally search by name/role or filter by exact role."""
    query = db.query(models.Profile)

    if search:
        term = f"%{search.lower()}%"
        query = query.filter(
            models.Profile.name.ilike(term) | models.Profile.target_role.ilike(term)
        )
    if role:
        query = query.filter(models.Profile.target_role == role)

    return query.order_by(models.Profile.created_at.desc()).all()


@router.get("/{profile_id}", response_model=schemas.ProfileOut)
def get_profile(profile_id: int, db: Session = Depends(get_db)):
    """Get a single profile by ID."""
    profile = db.query(models.Profile).filter(models.Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found.")
    return profile


@router.put("/{profile_id}", response_model=schemas.ProfileOut)
def update_profile(profile_id: int, payload: schemas.ProfileUpdate, db: Session = Depends(get_db)):
    """
    Update a profile. Any fields not provided are left unchanged.
    If projects are provided, they REPLACE the existing project list.
    Updating any profile field also deletes the saved analysis so it doesn't show stale results.
    """
    profile = db.query(models.Profile).filter(models.Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found.")

    changed = False

    if payload.name is not None:
        profile.name = payload.name.strip()
        changed = True
    if payload.skills is not None:
        profile.skills = [s.strip() for s in payload.skills if s.strip()]
        changed = True
    if payload.experience_level is not None:
        profile.experience_level = payload.experience_level
        changed = True
    if payload.target_role is not None:
        profile.target_role = payload.target_role.strip()
        changed = True
    if payload.timeline_mode is not None:
        profile.timeline_mode = payload.timeline_mode
        profile.timeline_days = payload.timeline_days  # can be None for relaxed
        changed = True
    if payload.projects is not None:
        # Replace project list
        db.query(models.Project).filter(models.Project.profile_id == profile_id).delete()
        for proj in payload.projects:
            db.add(models.Project(profile_id=profile_id, description=proj.description))
        changed = True

    if changed:
        if profile.analysis:
            db.delete(profile.analysis)

    db.commit()
    db.refresh(profile)
    return profile


@router.delete("/{profile_id}", status_code=200)
def delete_profile(profile_id: int, db: Session = Depends(get_db)):
    """Delete a profile and all its associated projects and analysis."""
    profile = db.query(models.Profile).filter(models.Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found.")
    db.delete(profile)
    db.commit()
    return {"status": "deleted", "profile_id": profile_id}
