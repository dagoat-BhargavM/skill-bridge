from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, field_validator, model_validator
from datetime import datetime


class ProjectCreate(BaseModel):
    description: str

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Project description cannot be empty.")
        if len(v) < 10:
            raise ValueError("Project description is too short — add a bit more context.")
        return v


class ProjectOut(BaseModel):
    id: int
    description: str

    model_config = {"from_attributes": True}


VALID_EXPERIENCE_LEVELS = {"entry", "mid", "senior"}
VALID_TIMELINE_MODES = {"relaxed", "deadline"}


class ProfileCreate(BaseModel):
    name: str
    skills: list[str]
    experience_level: str
    target_role: str
    timeline_mode: str = "relaxed"
    timeline_days: Optional[int] = None
    projects: list[ProjectCreate] = []

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty.")
        return v

    @field_validator("skills")
    @classmethod
    def skills_not_empty(cls, v: list[str]) -> list[str]:
        cleaned = [s.strip() for s in v if s.strip()]
        if not cleaned:
            raise ValueError("At least one skill is required.")
        return cleaned

    @field_validator("experience_level")
    @classmethod
    def valid_experience(cls, v: str) -> str:
        if v not in VALID_EXPERIENCE_LEVELS:
            raise ValueError(f"experience_level must be one of: {VALID_EXPERIENCE_LEVELS}")
        return v

    @field_validator("target_role")
    @classmethod
    def target_role_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Target role cannot be empty.")
        return v

    @field_validator("timeline_mode")
    @classmethod
    def valid_timeline_mode(cls, v: str) -> str:
        if v not in VALID_TIMELINE_MODES:
            raise ValueError(f"timeline_mode must be 'relaxed' or 'deadline'.")
        return v

    @field_validator("timeline_days")
    @classmethod
    def days_positive(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 1:
            raise ValueError("timeline_days must be at least 1.")
        return v

    @model_validator(mode="after")
    def deadline_requires_days(self) -> ProfileCreate:
        if self.timeline_mode == "deadline" and self.timeline_days is None:
            raise ValueError("timeline_days is required when timeline_mode is 'deadline'.")
        if self.timeline_mode == "relaxed":
            self.timeline_days = None   # enforce null for relaxed regardless of what was sent
        return self


class ProfileUpdate(BaseModel):
    """All fields optional — only provided fields will be updated."""
    name: Optional[str] = None
    skills: Optional[list[str]] = None
    experience_level: Optional[str] = None
    target_role: Optional[str] = None
    timeline_mode: Optional[str] = None
    timeline_days: Optional[int] = None
    projects: Optional[list[ProjectCreate]] = None


class ProfileOut(BaseModel):
    id: int
    name: str
    skills: list[str]
    experience_level: str
    target_role: str
    timeline_mode: str
    timeline_days: Optional[int]
    projects: list[ProjectOut]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AnalysisOut(BaseModel):
    profile_id: int
    match_percentage: int
    matching_skills: list[str]
    project_derived_skills: list[str]
    missing_critical: list[str]
    missing_preferred: list[str]
    strengths: list[str]
    recommendations: list[str]
    estimated_learning_times: dict[str, str]
    roadmap_type: str
    roadmap: Optional[list] = None   # list of roadmap nodes with resources (None for old records)
    source: str     # "gemini" | "fallback" — shown in the UI for transparency
    created_at: datetime

    model_config = {"from_attributes": True}
