"""Tests for the Mergington High School Activities API"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app import app

client = TestClient(app)


class TestRoot:
    """Test the root endpoint"""

    def test_root_redirect(self):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Test the get activities endpoint"""

    def test_get_activities_returns_dict(self):
        """Test that get activities returns a dictionary"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_activities_has_required_activities(self):
        """Test that activities have required fields"""
        response = client.get("/activities")
        data = response.json()
        
        # Check that we have activities
        assert len(data) > 0
        
        # Check structure of first activity
        for name, activity in data.items():
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity
            assert isinstance(activity["participants"], list)


class TestSignup:
    """Test the signup endpoint"""

    def test_signup_successful(self):
        """Test successful signup"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@example.com"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@example.com" in data["message"]

    def test_signup_duplicate_fails(self):
        """Test that duplicate signup fails"""
        email = "duplicate@example.com"
        # First signup
        response1 = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity(self):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@example.com"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]


class TestUnregister:
    """Test the unregister endpoint"""

    def test_unregister_successful(self):
        """Test successful unregistration"""
        email = "unregister@example.com"
        
        # First signup
        client.post(f"/activities/Drama%20Club/signup?email={email}")
        
        # Then unregister
        response = client.delete(
            f"/activities/Drama%20Club/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]

    def test_unregister_not_registered(self):
        """Test unregister for someone not registered"""
        response = client.delete(
            "/activities/Art%20Studio/unregister?email=notregistered@example.com"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]

    def test_unregister_nonexistent_activity(self):
        """Test unregister from non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent%20Activity/unregister?email=test@example.com"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]


class TestIntegration:
    """Integration tests"""

    def test_signup_then_verify_in_activities(self):
        """Test that signup adds participant to activity"""
        email = "integration@example.com"
        activity = "Programming%20Class"
        
        # Signup
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify by fetching activities
        response = client.get("/activities")
        data = response.json()
        activities = data["Programming Class"]["participants"]
        assert email in activities

    def test_signup_unregister_then_verify(self):
        """Test full lifecycle: signup -> unregister -> verify"""
        email = "lifecycle@example.com"
        activity = "Tennis%20Club"
        
        # Signup
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify signup
        response = client.get("/activities")
        data = response.json()
        assert email in data["Tennis Club"]["participants"]
        
        # Unregister
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200
        
        # Verify unregister
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Tennis Club"]["participants"]
