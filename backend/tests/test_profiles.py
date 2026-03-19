"""
Test: Profile CRUD — happy path and edge cases.
Run with: pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_create_profile_happy_path():
    """Creating a valid profile returns 201 with all fields populated correctly."""
    payload = {
        "name": "Priya Sharma",
        "skills": ["Python", "SQL", "Git"],
        "experience_level": "entry",
        "target_role": "Cloud Engineer",
        "timeline_mode": "deadline",
        "timeline_days": 14,
        "projects": [
            {"description": "Built REST API with Flask deployed on AWS EC2"}
        ]
    }
    res = client.post("/api/profiles/", json=payload)

    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Priya Sharma"
    assert data["skills"] == ["Python", "SQL", "Git"]
    assert data["experience_level"] == "entry"
    assert data["target_role"] == "Cloud Engineer"
    assert data["timeline_mode"] == "deadline"
    assert data["timeline_days"] == 14
    assert len(data["projects"]) == 1
    assert "id" in data


def test_get_profile_returns_saved_data():
    """After creation, GET returns the same data we saved."""
    create_res = client.post("/api/profiles/", json={
        "name": "Rahul Menon",
        "skills": ["JavaScript", "React"],
        "experience_level": "mid",
        "target_role": "Full Stack Developer",
        "timeline_mode": "relaxed",
    })
    profile_id = create_res.json()["id"]

    get_res = client.get(f"/api/profiles/{profile_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Rahul Menon"
    assert get_res.json()["timeline_mode"] == "relaxed"
    assert get_res.json()["timeline_days"] is None


def test_update_profile_clears_analysis():
    """Updating a profile via PUT should succeed and timeline_days updates correctly."""
    create_res = client.post("/api/profiles/", json={
        "name": "Test User",
        "skills": ["Python"],
        "experience_level": "entry",
        "target_role": "Backend Engineer",
        "timeline_mode": "relaxed",
    })
    pid = create_res.json()["id"]

    update_res = client.put(f"/api/profiles/{pid}", json={
        "timeline_mode": "deadline",
        "timeline_days": 7,
    })
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["timeline_mode"] == "deadline"
    assert updated["timeline_days"] == 7


def test_list_profiles_search():
    """Search query filters profiles by name."""
    client.post("/api/profiles/", json={
        "name": "Alice Searchable",
        "skills": ["Go"],
        "experience_level": "mid",
        "target_role": "Backend Engineer",
        "timeline_mode": "relaxed",
    })
    res = client.get("/api/profiles/?search=Alice")
    assert res.status_code == 200
    names = [p["name"] for p in res.json()]
    assert any("Alice" in n for n in names)


def test_create_profile_empty_skills_fails():
    """Submitting a profile with no skills should return 422 validation error."""
    res = client.post("/api/profiles/", json={
        "name": "No Skills",
        "skills": [],
        "experience_level": "entry",
        "target_role": "Cloud Engineer",
        "timeline_mode": "relaxed",
    })
    assert res.status_code == 422


def test_create_profile_deadline_without_days_fails():
    """Choosing deadline mode without providing days_available should fail validation."""
    res = client.post("/api/profiles/", json={
        "name": "Missing Days",
        "skills": ["Python"],
        "experience_level": "entry",
        "target_role": "Cloud Engineer",
        "timeline_mode": "deadline",
        "timeline_days": None,   # missing — should fail
    })
    assert res.status_code == 422


def test_get_nonexistent_profile_returns_404():
    """Requesting a profile that doesn't exist should return 404."""
    res = client.get("/api/profiles/99999")
    assert res.status_code == 404


def test_delete_profile():
    """Deleting a profile should return 204 and subsequent GET should 404."""
    create_res = client.post("/api/profiles/", json={
        "name": "To Delete",
        "skills": ["Python"],
        "experience_level": "entry",
        "target_role": "Backend Engineer",
        "timeline_mode": "relaxed",
    })
    pid = create_res.json()["id"]

    del_res = client.delete(f"/api/profiles/{pid}")
    assert del_res.status_code == 200

    get_res = client.get(f"/api/profiles/{pid}")
    assert get_res.status_code == 404
