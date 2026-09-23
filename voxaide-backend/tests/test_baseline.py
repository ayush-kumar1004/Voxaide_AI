import pytest
import json
import sys
import os

# Ensure voxaide-backend directory is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app

def test_health_check():
    """Verify that the backend /health endpoint returns 200 OK and healthy status."""
    client = app.test_client()
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data.get("status") == "healthy"
