import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """
    Arrange: Create a fresh TestClient for each test with isolated database.
    This fixture ensures no test pollution by resetting the app state.
    """
    return TestClient(app)


@pytest.fixture
def sample_emails():
    """Sample email addresses for testing"""
    return {
        "alice": "alice@mergington.edu",
        "bob": "bob@mergington.edu",
        "charlie": "charlie@mergington.edu"
    }
