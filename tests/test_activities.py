import pytest
from fastapi.testclient import TestClient


class TestRootEndpoint:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_index_html(self, client):
        # Arrange
        expected_redirect_url = "/static/index.html"

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert expected_redirect_url in response.headers["location"]


class TestGetActivitiesEndpoint:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        # Arrange
        expected_activity_keys = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) > 0
        assert "Chess Club" in activities
        for activity_name, activity_data in activities.items():
            assert activity_data.keys() == expected_activity_keys

    def test_get_activities_returns_correct_structure(self, client):
        # Arrange - no setup needed, pre-populated database exists

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert isinstance(activities, dict)
        chess_club = activities.get("Chess Club")
        assert chess_club is not None
        assert isinstance(chess_club["participants"], list)
        assert isinstance(chess_club["max_participants"], int)
        assert isinstance(chess_club["description"], str)

    def test_get_activities_participant_counts_accurate(self, client):
        # Arrange
        chess_club_expected_participants = 2

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert len(activities["Chess Club"]["participants"]) == chess_club_expected_participants


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant_success(self, client, sample_emails):
        # Arrange
        activity_name = "Basketball Team"
        email = sample_emails["alice"]

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert email in response.json()["message"]
        assert activity_name in response.json()["message"]

    def test_signup_verifies_participant_added_to_list(self, client, sample_emails):
        # Arrange
        activity_name = "Soccer Club"
        email = sample_emails["bob"]

        # Act - signup
        client.post(f"/activities/{activity_name}/signup", params={"email": email})

        # Assert - verify participant is in the list
        response = client.get("/activities")
        activities = response.json()
        assert email in activities[activity_name]["participants"]

    def test_signup_activity_not_found_returns_404(self, client, sample_emails):
        # Arrange
        activity_name = "Nonexistent Activity"
        email = sample_emails["alice"]

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_email_returns_400(self, client):
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"  # Already in Chess Club

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )

        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_duplicate_attempt_does_not_add_twice(self, client, sample_emails):
        # Arrange
        activity_name = "Art Club"
        email = sample_emails["charlie"]
        # First signup
        client.post(f"/activities/{activity_name}/signup", params={"email": email})

        # Act - attempt duplicate signup
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        activities = client.get("/activities").json()
        participant_count = activities[activity_name]["participants"].count(email)
        assert participant_count == 1

    def test_signup_with_special_characters_in_email(self, client):
        # Arrange
        activity_name = "Drama Club"
        email = "test+special@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        activities = client.get("/activities").json()
        assert email in activities[activity_name]["participants"]


class TestDeleteParticipantEndpoint:
    """Tests for DELETE /activities/{activity_name}/participants endpoint"""

    def test_delete_existing_participant_success(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club
        initial_count = len(client.get("/activities").json()[activity_name]["participants"])

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert email in response.json()["message"]
        activities = client.get("/activities").json()
        assert email not in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count - 1

    def test_delete_activity_not_found_returns_404(self, client):
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "test@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_delete_participant_not_found_returns_404(self, client):
        # Arrange
        activity_name = "Programming Class"
        email = "notinlist@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]

    def test_delete_cannot_remove_twice(self, client):
        # Arrange
        activity_name = "Gym Class"
        email = "john@mergington.edu"
        # First deletion succeeds
        client.delete(f"/activities/{activity_name}/participants", params={"email": email})

        # Act - attempt second deletion
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]

    def test_delete_only_removes_specified_participant(self, client):
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"
        email_to_keep = "daniel@mergington.edu"

        # Act
        client.delete(f"/activities/{activity_name}/participants", params={"email": email_to_remove})

        # Assert
        activities = client.get("/activities").json()
        assert email_to_remove not in activities[activity_name]["participants"]
        assert email_to_keep in activities[activity_name]["participants"]
