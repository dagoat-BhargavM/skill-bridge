from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    skills = Column(JSON, nullable=False, default=list)       # e.g. ["Python", "SQL", "Git"]
    experience_level = Column(String(20), nullable=False)     # "entry" | "mid" | "senior"
    target_role = Column(String(100), nullable=False)

    # Learning timeline — completely separate from projects
    timeline_mode = Column(String(20), nullable=False, default="relaxed")  # "relaxed" | "deadline"
    timeline_days = Column(Integer, nullable=True)             # None if relaxed

    projects = relationship("Project", back_populates="profile", cascade="all, delete-orphan")
    analysis = relationship("AnalysisResult", back_populates="profile", uselist=False, cascade="all, delete-orphan")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("Profile", back_populates="projects")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False, unique=True)

    match_percentage = Column(Integer, nullable=False)
    matching_skills = Column(JSON, default=list)
    project_derived_skills = Column(JSON, default=list)
    missing_critical = Column(JSON, default=list)
    missing_preferred = Column(JSON, default=list)
    strengths = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    estimated_learning_times = Column(JSON, default=dict)    # {"Docker": "3 days", ...}
    roadmap_type = Column(String(20), default="comprehensive") # "accelerated" | "comprehensive"
    roadmap = Column(JSON, default=list)                       # list of roadmap nodes with resources

    source = Column(String(50), nullable=False)               # "gemini" | "fallback"

    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("Profile", back_populates="analysis")
