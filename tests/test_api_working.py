import pytest
import os
from httpx import AsyncClient
from main import app
from db import database, init_db
from uuid import uuid4

pytestmark = pytest.mark.asyncio

@pytest.fixture(scope="session")
def init_database():
    print("Initializing database")
    init_db()  # Create tables using db.py's init_db
    yield
    print("Cleaning up database")
    try:
        os.remove("health_system.db")
    except FileNotFoundError:
        pass

@pytest.fixture(scope="session")
async def client(init_database):
    print("Creating client fixture")
    await database.connect()
    async_client = AsyncClient(app=app, base_url="http://test")
    yield async_client
    print("Closing client fixture")
    await async_client.aclose()
    await database.disconnect()

@pytest.fixture
async def auth_client(client):
    print("Creating auth_client fixture")
    email = f"test{uuid4()}@example.com"
    response = await client.post(
        "/auth/register",
        json={"email": email, "password": "testpass"}
    )
    assert response.status_code == 201, f"Register failed: {response.text}"
    response = await client.post(
        "/auth/jwt/login",
        data={"username": email, "password": "testpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    auth_client = AsyncClient(app=app, base_url="http://test")
    auth_client.headers.update({"Authorization": f"Bearer {token}"})
    yield auth_client
    print("Closing auth_client fixture")
    await auth_client.aclose()

async def test_register(client):
    print("Running test_register")
    email = f"newuser{uuid4()}@example.com"
    response = await client.post(
        "/auth/register",
        json={"email": email, "password": "newpass"}
    )
    assert response.status_code == 201, f"Register failed: {response.text}"
    assert response.json()["email"] == email

async def test_login(client):
    print("Running test_login")
    email = f"loginuser{uuid4()}@example.com"
    await client.post(
        "/auth/register",
        json={"email": email, "password": "loginpass"}
    )
    response = await client.post(
        "/auth/jwt/login",
        data={"username": email, "password": "loginpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    assert "access_token" in response.json()

async def test_create_program(auth_client):
    print("Running test_create_program")
    program_data = {"name": "TB Program", "description": "Tuberculosis treatment"}
    response = await auth_client.post("/api/programs", json=program_data)
    assert response.status_code == 201, f"Create program failed: {response.text}"
    assert response.json()["name"] == "TB Program"
    assert "program_id" in response.json()

async def test_create_client(auth_client):
    print("Running test_create_client")
    client_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "dob": "1985-05-15",
        "gender": "Female",
        "contact": "jane@example.com"
    }
    response = await auth_client.post("/api/clients", json=client_data)
    assert response.status_code == 201, f"Create client failed: {response.text}"
    assert response.json()["first_name"] == "Jane"
    assert "client_id" in response.json()

async def test_create_enrollment(auth_client):
    print("Running test_create_enrollment")
    program_data = {"name": "TB Program", "description": "Tuberculosis treatment"}
    program_response = await auth_client.post("/api/programs", json=program_data)
    assert program_response.status_code == 201, f"Create program failed: {program_response.text}"
    program_id = program_response.json()["program_id"]
    client_data = {
        "first_name": "John",
        "last_name": "Doe",
        "dob": "1990-01-01",
        "gender": "Male",
        "contact": "john@example.com"
    }
    client_response = await auth_client.post("/api/clients", json=client_data)
    assert client_response.status_code == 201, f"Create client failed: {client_response.text}"
    client_id = client_response.json()["client_id"]
    enrollment_data = {"client_id": str(client_id), "program_id": str(program_id)}
    response = await auth_client.post("/api/enrollments", json=enrollment_data)
    assert response.status_code == 201, f"Create enrollment failed: {response.text}"
    assert response.json()["client_id"] == client_id
    assert "enrollment_id" in response.json()