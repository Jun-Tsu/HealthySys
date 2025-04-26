import pytest
from fastapi.testclient import TestClient
from main import app
from db import database
from uuid import uuid4
from datetime import datetime

@pytest.fixture
async def client():
    """Create a FastAPI test client and connect to database."""
    await database.connect()
    yield TestClient(app)
    await database.disconnect()

@pytest.mark.asyncio
async def test_db_status(client):
    """Test the /db-status endpoint to ensure database is available."""
    response = client.get("/db-status")
    assert response.status_code == 200
    assert response.json()["status"] == "available"
    assert set(response.json()["tables"]) == {"programs", "clients", "enrollments"}
    assert response.json()["message"] == "Database is initialized and connected"

@pytest.mark.asyncio
async def test_create_program(client):
    """Test the /api/programs endpoint to create a program."""
    program_data = {"name": "TB Program", "description": "Tuberculosis treatment"}
    response = client.post("/api/programs", json=program_data)
    assert response.status_code == 201
    response_json = response.json()
    assert response_json["name"] == program_data["name"]
    assert response_json["description"] == program_data["description"]
    assert isinstance(response_json["program_id"], str)
    # Verify in database
    query = "SELECT * FROM programs WHERE program_id = :program_id"
    result = await database.fetch_one(query, {"program_id": response_json["program_id"]})
    assert result["name"] == program_data["name"]
    assert result["description"] == program_data["description"]

@pytest.mark.asyncio
async def test_create_enrollment(client):
    """Test the /api/enrollments endpoint to enroll a client in a program."""
    # Create a program
    program_data = {"name": "TB Program", "description": "Tuberculosis treatment"}
    program_response = client.post("/api/programs", json=program_data)
    program_id = program_response.json()["program_id"]

    # Create a client
    client_data = {
        "first_name": "John",
        "last_name": "Doe",
        "dob": "1990-01-01",
        "gender": "Male",
        "contact": "john@example.com"
    }
    client_response = client.post("/api/clients", json=client_data)
    client_id = client_response.json()["client_id"]

    # Create enrollment
    enrollment_data = {"client_id": client_id, "program_id": program_id}
    response = client.post("/api/enrollments", json=enrollment_data)
    assert response.status_code == 201
    response_json = response.json()
    assert response_json["client_id"] == client_id
    assert response_json["program_id"] == program_id
    assert isinstance(response_json["enrollment_id"], str)
    # Verify in database
    query = "SELECT * FROM enrollments WHERE enrollment_id = :enrollment_id"
    result = await database.fetch_one(query, {"enrollment_id": response_json["enrollment_id"]})
    assert result["client_id"] == client_id
    assert result["program_id"] == program_id