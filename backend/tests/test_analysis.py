"""
Test: Gap analysis — fallback logic and AI decision flow.
Run with: pytest tests/ -v
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app
from services.fallback_service import run_fallback

client = TestClient(app)


def _create_test_profile(**overrides):
    """Helper: create a profile and return its ID."""
    payload = {
        "name": "Test User",
        "skills": ["Python", "SQL", "Git", "Docker"],
        "experience_level": "entry",
        "target_role": "Cloud Engineer",
        "timeline_mode": "relaxed",
        "projects": [{"description": "Deployed a Flask app to AWS EC2"}],
        **overrides,
    }
    res = client.post("/api/profiles/", json=payload)
    assert res.status_code == 201
    return res.json()["id"]


def test_analysis_runs_and_is_persisted():
    """
    Happy path: POST /analyze/{id} runs (via fallback since no real API key in tests),
    returns a valid analysis, and GET /analyze/{id} then returns the same saved result.
    """
    pid = _create_test_profile()

    # Force fallback path since there's no real Gemini key in CI
    with patch("routes.analysis.call_gemini", return_value=None):
        post_res = client.post(f"/api/analyze/{pid}")

    assert post_res.status_code == 200
    data = post_res.json()

    # All required fields present
    for field in ["match_percentage", "matching_skills", "missing_critical",
                  "recommendations", "roadmap_type", "source"]:
        assert field in data, f"Missing field: {field}"

    assert data["source"] == "fallback"
    assert 0 <= data["match_percentage"] <= 100

    # Result should be persisted — GET should return same result
    get_res = client.get(f"/api/analyze/{pid}")
    assert get_res.status_code == 200
    assert get_res.json()["match_percentage"] == data["match_percentage"]


def test_analysis_deadline_mode_returns_accelerated():
    """
    Deadline mode should produce roadmap_type='accelerated' from fallback.
    """
    pid = _create_test_profile(timeline_mode="deadline", timeline_days=7)

    with patch("routes.analysis.call_gemini", return_value=None):
        res = client.post(f"/api/analyze/{pid}")

    assert res.status_code == 200
    assert res.json()["roadmap_type"] == "accelerated"


def test_fallback_triggers_when_gemini_returns_none():
    """If Gemini returns None (any failure), fallback runs and result is still valid."""
    pid = _create_test_profile()

    with patch("routes.analysis.call_gemini", return_value=None):
        res = client.post(f"/api/analyze/{pid}")

    assert res.status_code == 200
    assert res.json()["source"] == "fallback"


def test_fallback_triggers_when_gemini_returns_incomplete_json():
    """
    If Gemini returns a response missing required fields, we treat it as a failure
    and run the fallback instead. Handled in gemini_service._validate_response —
    simulated here by returning None (which is what call_gemini returns on failure).
    """
    pid = _create_test_profile()

    # Simulate Gemini returning an incomplete response (call_gemini returns None → fallback)
    with patch("routes.analysis.call_gemini", return_value=None):
        res = client.post(f"/api/analyze/{pid}")

    assert res.status_code == 200
    assert res.json()["source"] == "fallback"
    # All required fields must still be present even in fallback
    assert "recommendations" in res.json()
    assert isinstance(res.json()["recommendations"], list)


def test_analyze_nonexistent_profile_returns_404():
    """Analyzing a profile that doesn't exist should return 404."""
    with patch("routes.analysis.call_gemini", return_value=None):
        res = client.post("/api/analyze/99999")
    assert res.status_code == 404


def test_get_analysis_before_running_returns_404():
    """GET /analyze/{id} before any analysis is run should return 404."""
    pid = _create_test_profile()
    res = client.get(f"/api/analyze/{pid}")
    assert res.status_code == 404


def test_fallback_service_deadline_filters_skills():
    """
    Fallback with a 3-day deadline should only recommend skills learnable in ~2.4 days.
    Git (1 day) should be in recommendations, Kubernetes (10 days) should not.
    """
    result = run_fallback(
        user_skills=["Python"],
        target_role="Cloud Engineer",
        project_descriptions=[],
        timeline_mode="deadline",
        timeline_days=3,
    )
    assert result["roadmap_type"] == "accelerated"
    rec_text = " ".join(result["recommendations"]).lower()
    # Kubernetes takes 10 days — should NOT appear in a 3-day deadline roadmap
    assert "kubernetes" not in rec_text


def test_fallback_service_unknown_role():
    """Fallback with an unknown role should return a safe non-crashing response."""
    result = run_fallback(
        user_skills=["Python"],
        target_role="Quantum Wizard",   # not in job_roles.json
        project_descriptions=[],
        timeline_mode="relaxed",
        timeline_days=None,
    )
    assert result["match_percentage"] == 0
    assert len(result["recommendations"]) > 0  # should still return a helpful message
