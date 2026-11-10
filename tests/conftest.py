import os
import sys
import pytest
from unittest.mock import patch

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def client():
    """Sets up the Flask test client for API testing."""
    try:
        from app import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    except ImportError:
        yield None

@pytest.fixture(autouse=True)
def mock_external_apis():
    """Ensures no real external API calls are made during tests."""
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"events": []}
        yield mock_get