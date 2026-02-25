from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestRootEndpoint:
    """Test suite for GET / endpoint"""

    def test_root_redirects_to_static_index(self):
        # Arrange: Prepare client
        # Act: Make request to root endpoint
        response = client.get("/", follow_redirects=False)
        
        # Assert: Verify redirect response
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Test suite for GET /activities endpoint"""

    def test_get_all_activities_success(self):
        # Arrange: Activities are pre-populated in conftest
        # Act: Fetch all activities
        response = client.get("/activities")
        
        # Assert: Verify response contains all activities
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert len(data) == 9

    def test_activity_structure_is_correct(self):
        # Arrange: Request activities endpoint
        # Act: Get activities and check first one
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        # Assert: Verify required fields exist
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)

    def test_participants_are_returned(self):
        # Arrange: Chess Club has known participants
        # Act: Fetch activities
        response = client.get("/activities")
        data = response.json()
        
        # Assert: Verify participants list is correct
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]


class TestSignupForActivity:
    """Test suite for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant_success(self):
        # Arrange: Prepare new student email and activity
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        initial_count = len(client.get("/activities").json()[activity]["participants"])
        
        # Act: Sign up new participant
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        # Assert: Verify successful signup
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity}"
        
        # Assert: Verify participant was added
        updated_activity = client.get("/activities").json()[activity]
        assert email in updated_activity["participants"]
        assert len(updated_activity["participants"]) == initial_count + 1

    def test_signup_duplicate_participant_fails(self):
        # Arrange: Use an existing participant
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Act: Try to sign up the same participant twice
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        # Assert: Verify bad request error
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_nonexistent_activity_fails(self):
        # Arrange: Prepare invalid activity name
        email = "test@mergington.edu"
        activity = "Nonexistent Club"
        
        # Act: Try to sign up for activity that doesn't exist
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        # Assert: Verify not found error
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_multiple_different_participants(self):
        # Arrange: Two different emails and an activity
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        activity = "Art Studio"
        
        # Act: Sign up first participant
        response1 = client.post(
            f"/activities/{activity}/signup?email={email1}"
        )
        
        # Act: Sign up second participant
        response2 = client.post(
            f"/activities/{activity}/signup?email={email2}"
        )
        
        # Assert: Both signups successful
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Assert: Both participants in activity
        activity_data = client.get("/activities").json()[activity]
        assert email1 in activity_data["participants"]
        assert email2 in activity_data["participants"]


class TestRemoveParticipant:
    """Test suite for DELETE /activities/{activity_name}/{email} endpoint"""

    def test_remove_existing_participant_success(self):
        # Arrange: Get existing participant from Chess Club
        email = "michael@mergington.edu"
        activity = "Chess Club"
        initial_count = len(client.get("/activities").json()[activity]["participants"])
        
        # Act: Remove participant
        response = client.delete(f"/activities/{activity}/{email}")
        
        # Assert: Verify successful removal
        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email} from {activity}"
        
        # Assert: Verify participant was removed
        updated_activity = client.get("/activities").json()[activity]
        assert email not in updated_activity["participants"]
        assert len(updated_activity["participants"]) == initial_count - 1

    def test_remove_nonexistent_participant_fails(self):
        # Arrange: Use email that's not in the activity
        email = "notregistered@mergington.edu"
        activity = "Chess Club"
        
        # Act: Try to remove participant not in activity
        response = client.delete(f"/activities/{activity}/{email}")
        
        # Assert: Verify bad request error
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_remove_from_nonexistent_activity_fails(self):
        # Arrange: Prepare invalid activity name
        email = "test@mergington.edu"
        activity = "Nonexistent Club"
        
        # Act: Try to remove from activity that doesn't exist
        response = client.delete(f"/activities/{activity}/{email}")
        
        # Assert: Verify not found error
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_remove_all_participants_one_by_one(self):
        # Arrange: Tennis Club has one participant
        activity = "Tennis Club"
        email = "ryan@mergington.edu"
        
        # Act: Remove the only participant
        response = client.delete(f"/activities/{activity}/{email}")
        
        # Assert: Removal successful
        assert response.status_code == 200
        
        # Assert: Participants list is now empty
        activity_data = client.get("/activities").json()[activity]
        assert len(activity_data["participants"]) == 0
        assert email not in activity_data["participants"]
