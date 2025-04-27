import pytest
import os
from fastapi.testclient import TestClient
from main import app
from db import init_db
from uuid import uuid4
import asyncio

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def init_database():
    print("Initializing database")
    init_db()  # Create tables
    yield
    print("Cleaning up database")
    # Ensure all connections are closed before deleting
    if os.path.exists("health_system.db"):
        try:
            os.remove("health_system.db")
        except PermissionError:
            print("Could not delete health_system.db: file in use")

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
async def auth_client(client):
    email = f"testuser{uuid4()}@example.com"
    # Register user
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "testpass"}
    )
    assert response.status_code == 201, f"Registration failed: {response.text}"
    # Log in to get token
    response = client.post(
        "/auth/jwt/login",
        data={"username": email, "password": "testpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    yield client

@pytest.mark.asyncio
async def test_register(client, init_database):
    print("Running test_register")
    email = f"newuser{uuid4()}@example.com"
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "newpass"}
    )
    assert response.status_code == 201
    assert response.json()["email"] == email

@pytest.mark.asyncio
async def test_login(client, init_database):
    print("Running test_login")
    email = f"loginuser{uuid4()}@example.com"
    client.post(
        "/auth/register",
        json={"email": email, "password": "loginpass"}
    )
    response = client.post(
        "/auth/jwt/login",
        data={"username": email, "password": "loginpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_create_program(auth_client, init_database):
    print("Running test_create_program")
    program_data = {"name": "TB Program", "description": "Tuberculosis treatment"}
    response = auth_client.post("/api/programs", json=program_data)
    assert response.status_code == 201
    assert response.json()["name"] == "TB Program"

@pytest.mark.asyncio
async def test_create_client(auth_client, init_database):
    print("Running test_create_client")
    client_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "dob": "1985-05-15",
        "gender": "Female",
        "contact": "jane@example.com"
    }
    response = auth_client.post("/api/clients", json=client_data)
    assert response.status_code == 201
    assert response.json()["first_name"] == "Jane"

@pytest.mark.asyncio
async def test_create_enrollment(auth_client, init_database):
    print("Running test_create_enrollment")
    program_data = {"name": "TB Program", "description": "Tuberculosis treatment"}
    program_response = auth_client.post("/api/programs", json=program_data)
    assert program_response.status_code == 201
    program_id = program_response.json()["program_id"]
    client_data = {
        "first_name": "John",
        "last_name": "Doe",
        "dob": "1990-01-01",
        "gender": "Male",
        "contact": "john@example.com"
    }
    client_response = auth_client.post("/api/clients", json=client_data)
    assert client_response.status_code == 201
    client_id = client_response.json()["client_id"]
    enrollment_data = {"client_id": client_id, "program_id": program_id}
    response = auth_client.post("/api/enrollments", json=enrollment_data)
    assert response.status_code == 201
    assert response.json()["client_id"] == client_id