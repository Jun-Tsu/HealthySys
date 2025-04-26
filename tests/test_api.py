import pytest
from fastapi.testclient import TestClient
from main import app
from db import database
from uuid import uuid4
from datetime import datetime

# Set pytest-asyncio loop scope explicitly
pytestmark = pytest.mark.asyncio(loop_scope="function")

@pytest.fixture
def client():
    """Create a FastAPI test client and connect to database."""
    # Connect to database synchronously for simplicity in tests
    database.connect().get_loop().run_until_complete(database.connect())
    yield TestClient(app)
    database.disconnect().get_loop().run_until_complete(database.disconnect())

async def test_db_status(client):
    """Test the /db-status endpoint to ensure database is available."""
    response = client.get("/db-status")
    assert response.status_code == 200
    assert response.json()["status"] == "available"
    assert set(response.json()["tables"]) == {"programs", "clients", "enrollments"}
    assert response.json()["message"] == "Database is initialized and connected"

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

async def test_create_program_duplicate(client):
    """Test the /api/programs endpoint prevents duplicate program names."""
    program_data = {"name": "TB Program", "description": "Tuberculosis treatment"}
    # Create first program
    response = client.post("/api/programs", json=program_data)
    assert response.status_code == 201
    # Try to create duplicate
    response = client.post("/api/programs", json=program_data)
    assert response.status_code == 409
    assert "Program already exists" in response.json()["detail"]

async def test_create_client(client):
    """Test the /api/clients endpoint to create a client."""
    client_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "dob": "1985-05-15",
        "gender": "Female",
        "contact": "jane@example.com"
    }
    response = client.post("/api/clients", json=client_data)
    assert response.status_code == 201
    response_json = response.json()
    assert response_json["first_name"] == client_data["first_name"]
    assert response_json["last_name"] == client_data["last_name"]
    assert response_json["dob"] == client_data["dob"]
    assert response_json["gender"] == client_data["gender"]
    assert response_json["contact"] == client_data["contact"]
    assert isinstance(response_json["client_id"], str)
    assert response_json["programs"] == []
    # Verify in database
    query = "SELECT * FROM clients WHERE client_id = :client_id"
    result = await database.fetch_one(query, {"client_id": response_json["client_id"]})
    assert result["first_name"] == client_data["first_name"]
    assert result["last_name"] == client_data["last_name"]
    assert result["dob"] == client_data["dob"]
    assert result["gender"] == client_data["gender"]

async def test_create_client_duplicate(client):
    """Test the /api/clients endpoint prevents duplicate clients."""
    client_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "dob": "1985-05-15",
        "gender": "Female",
        "contact": "jane@example.com"
    }
    # Create first client
    response = client.post("/api/clients", json=client_data)
    assert response.status_code == 201
    # Try to create duplicate
    response = client.post("/api/clients", json=client_data)
    assert response.status_code == 409
    assert "Client already exists" in response.json()["detail"]

async def test_create_enrollment(client):
    """Test the /api/enrollments endpoint to enroll a client in a program."""
    # Create a program
    program_data = {"name": "TB Program", "description": "Tuberculosis treatment"}
    program_response = client.post("/api/programs", json=program_data)
    assert program_response.status_code == 201
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
    assert client_response.status_code == 201
    client_id = client_response.json()["client_id"]

    # Create enrollment
    enrollment_data = {"client_id": client_id, "program_id": program_id}
    response = client.post("/api/enrollments", json=enrollment_data)
    assert response.status_code == 201
    response_json = response.json()
    assert response_json["client_id"] == client_id
    assert response_json["program_id"] == program_id
    assert isinstance(response_json["enrollment_id"], str)
    assert "enrollment_date" in response_json
    # Verify in database
    query = "SELECT * FROM enrollments WHERE enrollment_id = :enrollment_id"
    result = await database.fetch_one(query, {"enrollment_id": response_json["enrollment_id"]})
    assert result["client_id"] == client_id
    assert result["program_id"] == program_id
    assert result["enrollment_date"]

async def test_create_enrollment_duplicate(client):
    """Test the /api/enrollments endpoint prevents duplicate enrollments."""
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

    # Create first enrollment
    enrollment_data = {"client_id": client_id, "program_id": program_id}
    response = client.post("/api/enrollments", json=enrollment_data)
    assert response.status_code == 201
    # Try to create duplicate
    response = client.post("/api/enrollments", json=enrollment_data)
    assert response.status_code == 409
    assert "Enrollment already exists" in response.json()["detail"]

async def test_search_clients(client):
    """Test the /api/clients/search endpoint to search clients by name."""
    # Create a client
    client_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "dob": "1985-05-15",
        "gender": "Female",
        "contact": "jane@example.com"
    }
    client_response = client.post("/api/clients", json=client_data)
    client_id = client_response.json()["client_id"]

    # Search for client
    search_data = {"search_term": "Jane"}
    response = client.post("/api/clients/search", json=search_data)
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json) >= 1
    client = next((c for c in response_json if c["client_id"] == client_id), None)
    assert client is not None
    assert client["first_name"] == "Jane"
    assert client["last_name"] == "Smith"
    assert client["dob"] == "1985-05-15"
    assert client["gender"] == "Female"
    assert client["contact"] == "jane@example.com"
    assert client["programs"] == []

async def test_get_client_profile(client):
    """Test the /api/clients/{client_id} endpoint to get client profile."""
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

    # Enroll client in program
    enrollment_data = {"client_id": client_id, "program_id": program_id}
    client.post("/api/enrollments", json=enrollment_data)

    # Get client profile
    response = client.get(f"/api/clients/{client_id}")
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["client_id"] == client_id
    assert response_json["first_name"] == "John"
    assert response_json["last_name"] == "Doe"
    assert response_json["dob"] == "1990-01-01"
    assert response_json["gender"] == "Male"
    assert response_json["contact"] == "john@example.com"
    assert len(response_json["programs"]) == 1
    assert response_json["programs"][0]["program_id"] == program_id
    assert response_json["programs"][0]["name"] == "TB Program"